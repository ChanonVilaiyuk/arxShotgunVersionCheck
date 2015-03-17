#Import python modules
import sys, os, re, shutil, random, sip

sys.path.append('U:/extensions/studioTools')
sys.path.append('U:/extensions/studioTools/python')
from PyQt4 import QtCore, QtGui

#Import GUI
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from arxShotgunVersionCheck import ui
reload(ui)

from sgUtils import sgUtils
reload(sgUtils)

from tools.utils import fileUtils
reload(fileUtils)


class MyForm(QtGui.QMainWindow):

	def __init__(self, parent=None):
		self.count = 0
		#Setup Window
		QtGui.QWidget.__init__(self, parent)
		self.ui = ui.Ui_ShotgunVersionWindow()
		self.ui.setupUi(self)

		# column
		self.statusColumn = 0
		self.actionColumn = 1
		self.shotColumn = 2 
		self.stepColumn = 3 
		self.taskColumn = 4 
		self.shotgunColumn = 5
		self.serverColumn = 6
		self.publishColumn = 7 
		self.convertColumn = 8

		# media path
		self.mediaPath = 'V:/projects'

		# color
		self.green = [100, 255, 100]
		self.red = [255, 100, 100]
		self.yellow = [255, 200, 0]
		self.orange = [255, 140, 40]

		# sg data
		self.shotVersionInfo = dict()
		self.shotInfo = dict()
		self.serverShotInfo = dict()
		self.allInfo = dict()


		self.initFunctions()
		self.initConnections()



	def initFunctions(self) : 
		self.listProjects()
		self.resizeColumn()



	def initConnections(self) : 
		self.ui.getData_pushButton.clicked.connect(self.doScanShot)
		self.ui.update_pushButton.clicked.connect(self.doUpdate)



	def listProjects(self) : 
		# sg command
		projects = sgUtils.sg.find('Project', filters=[], fields=['name'])

		self.ui.project_comboBox.clear()

		for eachProject in projects : 
			projectName = eachProject['name']
			self.ui.project_comboBox.addItem(projectName)



	def getSGShotInfo(self) : 

		# project 
		project = str(self.ui.project_comboBox.currentText())
		project = 'ttv_e100'
		filters = [['project.Project.name', 'is', project]]
		fields = ['code', 'id']
		shots = sgUtils.sg.find('Shot', filters, fields)

		for each in shots : 
			shotName = each['code']
			self.shotInfo[shotName] = {'code': shotName, 'id': each['id']}

		return shots



	def getSGVersionInfo(self) : 

		versions = self.getSGVersion()
		shotVersionInfo = dict()
		maxVer = 0

		for eachVersion in sorted(versions) : 
			versionName = eachVersion['code']
			entity = eachVersion['entity']
			shotName = None
			uploadMovie = eachVersion['sg_uploaded_movie']
			shotID = eachVersion['entity']
			taskID = eachVersion['sg_task']
			taskStatus = eachVersion['sg_task.Task.sg_status_list']
			currentVer = None

			if entity : 
				shotName = entity['name']

				if uploadMovie : 
					uploadMovie = eachVersion['sg_uploaded_movie']['name']
					currentVer = self.findVersion(uploadMovie)

					# if shotName not in the dict, just add
					if not shotName in shotVersionInfo.keys() : 
						shotVersionInfo[shotName] = {'versionName': versionName, 'versionId': eachVersion['id'], 'uploadMovie': uploadMovie, 'shotID': shotID, 'taskID': taskID, 'taskStatus': taskStatus}

					# if already in the dict, see if the new one really a higher version
					else : 
						previousVersion = shotVersionInfo[shotName]['versionName']
						previousVersionNumber = self.findVersion(previousVersion)

						# if higher version, replace previous data
						if currentVer > previousVersionNumber : 
							shotVersionInfo[shotName] = {'versionName': versionName, 'versionId': eachVersion['id'], 'uploadMovie': uploadMovie, 'shotID': shotID, 'taskID': taskID, 'taskStatus': taskStatus}


		self.shotVersionInfo = shotVersionInfo

		return shotVersionInfo


	def getSGVersion(self) : 

		# project 
		project = str(self.ui.project_comboBox.currentText())
		project = 'ttv_e100'
		filters = [['project.Project.name', 'is', project]]
		fields = ['code', 'id', 'entity', 'sg_task', 'sg_uploaded_movie', 'sg_task.Task.sg_status_list']
		versions = sgUtils.sg.find('Version', filters, fields)


		return versions


	def getServerVersionInfo(self) : 
		# project 
		project = str(self.ui.project_comboBox.currentText())
		project = 'ttv_e100'
		episode = project.split('_')[-1]
		serverPath = '%s/ttv/%s/shotgun' % (self.mediaPath, episode) 
		serverShotInfo = dict()


		if os.path.exists(serverPath) : 
			movs = fileUtils.listFile(serverPath, 'mov')

			for eachMov in movs : 
				eles = eachMov.split('_')
				shotName = ('_').join(eles[1:4])
				dep = eles[-1].split('.')[0]
				eachMov = '%s/%s' % (serverPath, eachMov)

				# ttv_e100_010_010_layout.v014.mov
				# get version by split . and remove "v"
				strVersion = eachMov.split('.')[1].replace('v', '')
				if strVersion.isdigit() : 
					version = int(strVersion)

				# if not assign yet, assign 
				if not shotName in serverShotInfo.keys() : 
					serverShotInfo[shotName] = {dep: eachMov}

				# if already assigned, check for highest version
				else : 
					# check first if anim or layout 
					if not dep in serverShotInfo[shotName].keys() : 
						serverShotInfo[shotName].update({dep: eachMov})

					# if dep already in anim or layout 
					else : 
						# if new shot has higher version, replace existing 
						existsVersion = int(serverShotInfo[shotName][dep].split('.')[1].replace('v', ''))

						if version > existsVersion : 
							serverShotInfo[shotName].update({dep: eachMov})


		self.serverShotInfo = serverShotInfo
		return serverShotInfo
		# for each in sorted(serverShotInfo) : 
		# 	print each, serverShotInfo[each]



	def getPublishVersionInfo(self) : 
		# project 
		project = str(self.ui.project_comboBox.currentText())
		project = 'ttv_e100'
		episode = project.split('_')[-1]
		serverPath = '%s/ttv/%s' % (self.mediaPath, episode) 
		publishInfo = dict()
		
		seqs = fileUtils.listFolder(serverPath)

		for eachSeq in seqs : 
			browseShot = '%s/%s' % (serverPath, eachSeq)
			shots = fileUtils.listFolder(browseShot)

			for eachShot in shots : 
				browseDep = '%s/%s' % (browseShot, eachShot)
				deps = fileUtils.listFolder(browseDep)

				for eachDep in deps : 
					browseFile = '%s/%s' % (browseDep, eachDep)
					files = fileUtils.listFile(browseFile)
					maxVersion = None

					for eachFile in files : 
						version = self.findVersion(eachFile)
						dep = eachFile.split('_')[-1].split('.')[0]

						if version > max : 
							maxVersion = eachFile

					if maxVersion : 
						shotName = ('_').join(maxVersion.split('_')[1:4])

						if not shotName in publishInfo.keys() : 
							publishInfo[shotName] = {dep: maxVersion, 'path': browseFile}

						else : 
							if not dep in publishInfo[shotName].keys() : 
								publishInfo[shotName].update({dep: maxVersion, 'path': browseFile})


		return publishInfo
		# for each in sorted(publishInfo) : 
		# 	print each, publishInfo[each]




	# button action =======================================================================================

	def doScanShot(self) : 
		self.listData()
		self.resizeColumn()


	def listData(self) : 
		row = 0
		height = 20
		widget = 'shotgun_tableWidget'
		shotInfo = dict()
		color = [255, 255, 255]

		self.ui.status_label.setText('Listing shot ...')
		QtGui.QApplication.processEvents()

		shots = self.getSGShotInfo()
		shotVersionInfo = self.getSGVersionInfo()
		serverVersionInfo = self.getServerVersionInfo()
		publishVersionInfo = self.getPublishVersionInfo()

		self.clearTable(widget)

		# self.writeLog(str(shotVersionInfo))


		for eachShot in sorted(shots) : 
			status = '-'
			shotName = eachShot['code']
			versionName = '-'
			uploadMovie = '-'
			serverMovie = '-'
			publishMovie = '-'
			convert = '-'
			action = '-'
			statusColor = color
			convertColor = color
			sgTask = '-'
			dep = None
			sgTaskStep = ''
			sgStep = ''
			svStep = ''

			# get update task
			updateTask = self.getUpdateTask(shotName)

			# get version from shotgun
			if shotName in shotVersionInfo.keys() : 
				versionName = shotVersionInfo[shotName]['versionName']
				uploadMovie = shotVersionInfo[shotName]['uploadMovie']
				if shotVersionInfo[shotName]['taskID'] : 
					sgTask = shotVersionInfo[shotName]['taskID']['name']
					

				if not uploadMovie : 
					uploadMovie = 'N/A'

				shotInfo[shotName] = {'id': eachShot['id']}

			# get mov file from server
			if shotName in serverVersionInfo.keys() : 

				# find department -> anim or layout
				if uploadMovie : 
					dep = uploadMovie.split('_')[-1].split('.')[0]

					if dep in serverVersionInfo[shotName].keys() : 
						serverMovie = serverVersionInfo[shotName][dep]
						sgStep = dep

					else : 
						if 'anim' in serverVersionInfo[shotName].keys() : 
							serverMovie = serverVersionInfo[shotName]['anim']
							sgStep = 'anim'

						elif 'layout' in serverVersionInfo[shotName].keys() : 
							serverMovie = serverVersionInfo[shotName]['layout']
							sgStep = 'layout'

						else : 
							serverMovie = 'N/A'
							sgStep = 'N/A'

				else : 
					if 'anim' in serverVersionInfo[shotName].keys() : 
						serverMovie = serverVersionInfo[shotName]['anim']
						svStep = 'anim'

					elif 'layout' in serverVersionInfo[shotName].keys() : 
						serverMovie = serverVersionInfo[shotName]['layout']
						svStep = 'layout'

					else : 
						serverMovie = 'N/A'
						svStep = 'N/A'


			# get publish file from server
			if shotName in publishVersionInfo.keys() : 

				# find department -> anim or layout
				if uploadMovie : 
					dep = uploadMovie.split('_')[-1].split('.')[0]

					if dep in publishVersionInfo[shotName].keys() : 
						publishMovie = publishVersionInfo[shotName][dep]
						sgStep = dep

					else : 
						if 'anim' in publishVersionInfo[shotName] : 
							publishMovie = publishVersionInfo[shotName]['anim']
							sgStep = 'anim'

						elif 'layout' in publishVersionInfo[shotName] : 
							publishMovie = publishVersionInfo[shotName]['layout']
							sgStep = 'layout'

						else : 
							publishMovie = 'N/A'


				else : 
					if 'anim' in publishVersionInfo[shotName] : 
						publishMovie = publishVersionInfo[shotName]['anim']
						svStep = 'anim'

					elif 'layout' in publishVersionInfo[shotName] : 
						publishMovie = publishVersionInfo[shotName]['layout']
						svStep = 'layout'

					else : 
						publishMovie = 'N/A'

			
			# define department 
			if sgTaskStep : 
				dep = sgTaskStep 

			elif sgStep : 
				if not sgStep == 'N/A' : 
					dep = sgStep 

			elif svStep : 
				if not svStep == 'N/A' : 
					dep = svStep

			else : 
				dep = 'N/A'


			# compare shotgun and server version
			serverMovieName = os.path.basename(serverMovie)

			if uploadMovie == serverMovieName : 
				if not uploadMovie == '-' : 
					action = 'Good'
					statusColor = self.green

				else : 
					action = '-'

			else : 
				# see version
				uploadVersion = self.findVersion(uploadMovie)
				serverVersion = self.findVersion(serverMovieName)
				publishVersion = self.findVersion(publishMovie)


				# if both of them return version
				if uploadVersion and serverVersion : 

					# if server is newer
					if int(serverVersion) > int(uploadVersion) : 
						action = 'Need upload'
						statusColor = self.red

					# if shotgun is newer 
					if int(serverVersion) < int(uploadVersion) : 
						action = 'Email coordinator'
						statusColor = self.yellow

				elif uploadVersion : 
					if not publishVersion : 
						action = 'Shotgun newer'
						statusColor = self.orange

					else : 
						if int(publishVersion) == int(uploadVersion) : 
							action = 'Good'
							statusColor = self.green

						if int(publishVersion) > int(uploadVersion) : 
							action = 'Need upload*'
							statusColor = self.red
							convert = 'Yes'
							convertColor = self.green

						elif int(publishVersion) < int(uploadVersion) : 
							action = 'Email coordinator'
							statusColor = self.yellow



				elif serverVersion : 
					action = 'Need upload'
					statusColor = self.red

				else : 
					action = '-'


			datas = {	
						'status': {'text': status, 'color': color},
						'shotName': {'text': shotName, 'color': color},
						'uploadMovie': {'text': uploadMovie, 'color': color},
						'serverMovie': {'text': serverMovieName, 'color': color},
						'publishMovie': {'text': publishMovie, 'color': color},
						'convert': {'text': convert, 'color': convertColor},
						'action': {'text': action, 'color': statusColor},
						'step': {'text': dep, 'color': statusColor},
						'task': {'text': updateTask, 'color': color}
					}

			self.fillData(row, datas)
			# self.allInfo[shotName] = {'serverMovie': }

			row += 1 

		self.ui.status_label.setText('')
		QtGui.QApplication.processEvents()


	def doUpdate(self) : 
		if not self.ui.all_checkBox.isChecked() : 
			widget = 'shotgun_tableWidget'

			# get data from table
			actions = self.getDataFromSelectedRange(self.actionColumn, widget)
			shots = self.getDataFromSelectedRange(self.shotColumn, widget)
			serverFiles = self.getDataFromSelectedRange(self.serverColumn, widget)
			publishFiles = self.getDataFromSelectedRange(self.publishColumn, widget)
			step = self.getDataFromSelectedRange(self.stepColumn, widget)

			row = 0
			i = 0

			for action in actions : 
				shotName = shots[i]
				serverFile = serverFiles[i]
				publishFile = publishFiles[i]
				self.serverShotInfo[shotName]

				if action == 'Good' : 
					pass 

				if action == 'Need upload' : 
					self.updateSG(shotName, serverFile, step)
					# self.setStatus(self.statusColumn, i, True)
					self.doScanShot()

				if action == 'Need upload*' : 
					self.convertMov()
					self.updateSG()
					# self.setStatus()
					self.doScanShot()

				row += 1
				i += 1


	# sub function from button ===========================================================================================

	def getUpdateTask(self, shotName) : 

		updateTask = None
		# if shotName has version, find task related to this version
		if shotName in self.shotVersionInfo.keys() : 
			versionInfo = self.shotVersionInfo[shotName]
			taskInfo = versionInfo['taskID']
			shotInfo = versionInfo['shotID']
			taskStatus = versionInfo['taskStatus']

			# if task linked to version, find what task 
			if taskInfo : 
				taskID = taskInfo['id']
				taskName = taskInfo['name']

				if taskName == 'anim_blocking' : 
					# check status first

					# if status = aeo7, mean blocking is approved. update anim_splining instead. 
					if taskStatus == 'aeo7' : 
						updateTask = 'anim_splining'

					else : 
						updateTask = 'anim_blocking'

				if taskName == 'anim_splining' : 
					updateTask = 'anim_splining'

			# if not task assosiated, assign to blocking
			else : 
				updateTask = 'anim_splining'

		# if no version, assign to blocling
		else : 
			updateTask = 'anim_blocking'

		return updateTask




	def updateSG(self, shotName, movieFile, step) : 

		taskID = None
		shotID = None
		setTaskStatus = 'rev'
		versionName = movieFile.replace('.mov', '')
		projectName = str(self.ui.project_comboBox.currentText())

		# if shotName has version, get taskID, shotID from version data
		if shotName in self.shotVersionInfo.keys() : 
			versionInfo = self.shotVersionInfo[shotName]
			taskInfo = versionInfo['taskID']
			shotInfo = versionInfo['shotID']
			taskStatus = versionInfo['taskStatus']

			if taskInfo : 
				taskID = taskInfo['id']
				taskName = taskInfo['name']

			if shotInfo : 
				shotID = shotInfo['id']

			print taskID, shotID, taskName, taskStatus

			if step == 'layout' : 
				if taskName == 'layout' : 
					# update layout
					self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)

			if step == 'anim' : 

				if taskName == 'anim_blocking' : 
					
					# update splining 
					if taskStatus == 'aeo7' : 
						task = 'anim_splining'
						result = self.findTaskID(projectName, shotName, task)
						taskID = result[0]['id']

						if taskID : 
							self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)

						else : 
							self.completeDialog('Error', 'No taskID for %s, %s, %s' % (projectName, shotName, task))


					# update blocking
					else : 
						task = 'anim_blocking'
						self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)


				if taskName == 'anim_splining' : 
					task = 'anim_splining'
					self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)

		# no version data, get shotID and taskID by calling shotgun
		else : 
			if shotName in self.shotInfo.keys() : 
				task = None

				if step == 'layout' : 
					task = 'layout'

				if step == 'anim' : 
					task = 'anim_blocking'

				if task : 
					shotID = self.shotInfo[shotName]['id']
					result = self.findTaskID(projectName, shotName, task)

					if result : 
						taskID = result[0]['id']
						self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)

					else : 
						self.completeDialog('Error', 'Cannot find task ID')



	def updateSGCmd(self, projectName, versionName, shotID, taskID, movieFile, status) : 
		print versionName, shotID, taskID, movieFile, status

		proj = sgUtils.sg.find_one('Project', [['name', 'is', projectName]])

		data = { 'project': proj,
				 'code': versionName,
				 'entity': {'type':'Shot', 'id':shotID},
				 'sg_task': {'type':'Task', 'id':taskID},
				 'sg_status_list': status, 
				 # 'sg_path': {'local_path': publishFile, 'name': version}

			 }

		print movieFile

		# result = sgUtils.sg.create('Version', data)
		# print 'Create version %s success' % versionName
		# result2 = sgUtils.sg.upload('Version', result['id'], movieFile.replace('/', '\\'), 'sg_uploaded_movie')
		# print 'Upload movie %s success' % movieFile
		# print '________________________________'

		# return result2


	def findTaskID(self, projName, shotName, taskName) : 
		print 'find, %s, %s, %s' % (projName, shotName, taskName)
		filters = [['project.Project.name', 'is', projName], ['entity.Shot.code', 'is', shotName], ['content', 'is', taskName]]    
		fields = ['code', 'id']
		result = sgUtils.sg.find('Task', filters, fields)

		return result


		# find taskID
		# fi

		# taskID = sgGetShotTaskID(projName, episode, sequenceName, shotName, taskName)
		# data = { 'project': proj,
		#  'code': pubVersion,
		#  'entity': {'type': 'Shot', 'id':shotID},
		#  'sg_task': {'type':'Task', 'id':taskID},
		#  'sg_status_list': status, 
		#  'description' : description }


		# result = sg.create('Version', data)
		# sg.upload('Version', versionId, movieFile, 'sg_uploaded_movie')


	def fillData(self, row, datas) : 
			status = datas['status']['text']
			shotName = datas['shotName']['text']
			uploadMovie = datas['uploadMovie']['text']
			serverMovie = datas['serverMovie']['text']
			publishMovie = datas['publishMovie']['text']
			convert = datas['convert']['text']
			action = datas['action']['text']
			step = datas['step']['text']
			task = datas['task']['text']

			statusColor = datas['status']['color']
			shotNameColor = datas['shotName']['color']
			uploadMovieColor = datas['uploadMovie']['color']
			serverMovieColor = datas['serverMovie']['color']
			publishMovieColor = datas['publishMovie']['color']
			convertColor = datas['convert']['color']
			actionColor = datas['action']['color']
			stepColor = datas['step']['color']
			taskColor = datas['task']['color']

			height = 20
			widget = 'shotgun_tableWidget'
			self.insertRow(row, height, widget)
			self.fillInTable(row, self.statusColumn, status, widget, statusColor)
			self.fillInTable(row, self.shotColumn , shotName, widget, shotNameColor)
			self.fillInTable(row, self.shotgunColumn, uploadMovie, widget, uploadMovieColor)
			self.fillInTable(row, self.serverColumn, serverMovie, widget, serverMovieColor)
			self.fillInTable(row, self.publishColumn , publishMovie, widget, publishMovieColor)
			self.fillInTable(row, self.convertColumn, convert, widget, convertColor)
			self.fillInTable(row, self.actionColumn, action, widget, actionColor)
			self.fillInTable(row, self.stepColumn, step, widget, stepColor)
			self.fillInTable(row, self.taskColumn, task, widget, taskColor)

			


	# widget part =========================================================================================

	def resizeColumn(self) : 
		self.ui.shotgun_tableWidget.resizeColumnToContents(self.statusColumn)
		self.ui.shotgun_tableWidget.resizeColumnToContents(self.shotColumn)
		self.ui.shotgun_tableWidget.resizeColumnToContents(self.stepColumn)
		self.ui.shotgun_tableWidget.resizeColumnToContents(self.taskColumn)
		# self.ui.shotgun_tableWidget.resizeColumnToContents(self.shotgunColumn)
		# self.ui.shotgun_tableWidget.resizeColumnToContents(self.serverColumn)
		# self.ui.shotgun_tableWidget.resizeColumnToContents(self.publishColumn)
		self.ui.shotgun_tableWidget.resizeColumnToContents(self.convertColumn)
		self.ui.shotgun_tableWidget.resizeColumnToContents(self.actionColumn)


	# general function =======================================================================

	def findVersion(self, inputFile) : 
		eles = inputFile.split('.')
		version = None

		for each in eles : 
			if each[0] == 'v' and each[1:].isdigit() : 
				version = each[1:]

		return version

	# table part ==========================================================================================

	def insertRow(self, row, height, widget) : 
		cmd1 = 'self.ui.%s.insertRow(row)' % widget
		cmd2 = 'self.ui.%s.setRowHeight(row, height)' % widget

		eval(cmd1)
		eval(cmd2)


	def fillInTable(self, row, column, text, widget, color = [1, 1, 1]) : 
		item = QtGui.QTableWidgetItem()
		item.setText(text)
		item.setBackgroundColor(QtGui.QColor(color[0], color[1], color[2]))
		cmd = 'self.ui.%s.setItem(row, column, item)' % widget
		eval(cmd)


	def fillInTableIcon(self, row, column, text, iconPath, widget, color = [1, 1, 1]) : 
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(iconPath), QtGui.QIcon.Normal, QtGui.QIcon.Off)

		item = QtGui.QTableWidgetItem()
		item.setText(str(text))
		item.setIcon(icon)
		item.setBackgroundColor(QtGui.QColor(color[0], color[1], color[2]))
		
		cmd = 'self.ui.%s.setItem(row, column, item)' % widget
		eval(cmd)


	def getAllData(self, columnNumber, widget) : 
		count = eval('self.ui.%s.rowCount()' % widget)
		items = []

		for i in range(count) : 
			item = str(eval('self.ui.%s.item(i, columnNumber).text()' % widget))
			items.append(item)


		return items


	def getDataFromSelectedRange(self, columnNumber, widget) : 
		lists = eval('self.ui.%s.selectedRanges()' % widget)

		if lists : 
			topRow = lists[0].topRow()
			bottomRow = lists[0].bottomRow()
			leftColumn = lists[0].leftColumn()
			rightColumn = lists[0].rightColumn()

			items = []

			for i in range(topRow, bottomRow + 1) : 
				item = str(eval('self.ui.%s.item(i, columnNumber)' % widget).text())
				items.append(item)


			return items


	def getSelectionRows(self, widget) : 
		lists = eval('self.ui.%s.selectedRanges()' % widget)

		if lists : 
			topRow = lists[0].topRow()
			bottomRow = lists[0].bottomRow()
			leftColumn = lists[0].leftColumn()
			rightColumn = lists[0].rightColumn()

			return [topRow, bottomRow, leftColumn, rightColumn]



	def clearTable(self, widget) : 
		cmd = 'self.ui.%s.rowCount()' % widget
		rows = eval(cmd)
		# self.ui.asset_tableWidget.clear()

		for each in range(rows) : 
			cmd2 = 'self.ui.%s.removeRow(0)' % widget
			eval(cmd2)



	def writeLog(self, data) : 
		fileUtils.writeFile('U:/extensions/studioTools/python/arxShotgunVersionCheck/log.txt', data)



	def completeDialog(self, title, dialog) : 
		QtGui.QMessageBox.information(self, title, dialog, QtGui.QMessageBox.Ok)



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())