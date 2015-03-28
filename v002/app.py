import sys, os, re, shutil, random

#Import python modules
sys.path.append('U:/extensions/studioTools')
sys.path.append('U:/extensions/studioTools/python')
sys.path.append('U:/extensions/python/2.7/win64/site-packages')

# from PyQt4 import QtCore, QtGui
# import sip

# #Import GUI
# from PyQt4.QtCore import *
# from PyQt4.QtGui import *

from PySide import QtCore
from PySide import QtGui

from arxShotgunVersionCheck import ui2 as ui
reload(ui)

from sgUtils import sgUtils
reload(sgUtils)

from tools.utils import fileUtils
reload(fileUtils)

moduleDir = sys.modules[__name__].__file__


class MyForm(QtGui.QMainWindow):

	def __init__(self, parent=None):
		self.count = 0
		#Setup Window
		super(MyForm, self).__init__(parent)
		self.ui = ui.Ui_ShotgunVersionWindow()
		self.ui.setupUi(self)

		# project setting
		self.frameRate = 24

		# logo
		self.iconDir = os.path.dirname(moduleDir).replace('\\', '/')
		self.logo = 'logo.png'
		self.okIcon = 'ok_icon.png'
		self.readyIcon = 'ready_icon.png'
		self.xIcon = 'x_icon.png'
		self.ipIcon = 'ip_icon.png'
		self.needAttention = 'attention_icon.png'
		self.convertIcon = 'convert_icon.png'

		# column
		self.statusColumn = 0
		self.actionColumn = 1
		self.shotColumn = 2 
		self.shotgunColumn = 3
		self.serverColumn = 4
		self.publishColumn = 5 
		self.stepColumn = 6 
		self.taskColumn = 7
		self.convertColumn = 8

		# media path
		self.mediaPath = 'V:/projects'

		# color
		self.white = [255, 255, 255]
		self.green = [100, 255, 100]
		self.lightGreen = [200, 255, 200]
		self.red = [255, 100, 100]
		self.lightRed = [255, 200, 200]
		self.yellow = [255, 200, 0]
		self.lightYellow = [255, 240, 40]
		self.orange = [255, 140, 40]
		self.lightOrange = [255, 200, 100]

		# sg data
		self.shotVersionInfo = dict()
		self.shotInfo = dict()
		self.serverShotInfo = dict()
		self.publishInfo = dict()
		self.allInfo = dict()


		self.initFunctions()
		self.initConnections()



	def initFunctions(self) : 
		self.setLogo()
		self.listProjects()
		self.resizeColumn()



	def initConnections(self) : 
		self.ui.getData_pushButton.clicked.connect(self.doScanShot)
		self.ui.update_pushButton.clicked.connect(self.doUpdate)



	def listProjects(self) : 
		# sg command
		projects = sgUtils.sg.find('Project', filters=[], fields=['name'])

		self.ui.project_comboBox.clear()
		projectList = []

		for eachProject in sorted(projects) : 
			projectName = eachProject['name']
			projectList.append(projectName)

		for eachProject in sorted(projectList) :
			self.ui.project_comboBox.addItem(projectName)



	def getSGShotInfo(self) : 

		# project 
		project = self.getProjectName()
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
		project = self.getProjectName()
		filters = [['project.Project.name', 'is', project]]
		fields = ['code', 'id', 'entity', 'sg_task', 'sg_uploaded_movie', 'sg_task.Task.sg_status_list']
		versions = sgUtils.sg.find('Version', filters, fields)


		return versions

	def getSGTaskInfo(self) : 

		pass
		# project 
		# project = self.getProjectName()
		# filters = [['project.Project.name', 'is', project]]
		# fields = ['content', 'id', 'entity', 'sg_status_list']
		# tasks = sgUtils.sg.find('Task', filters, fields)

		# taskInfo = dict()

		# for eachTask in tasks : 
		# 	shotName = eachTask['entity']

		# 	if eachTask['entity'] : 
		# 		shotName = eachTask['entity']['name']
		# 		taskName = eachTask['content']
		# 		status = eachTask['sg_status_list']
				
				
		# 		# if task is blocking
		# 		if taskName == 'anim_blocking' : 
		# 			# if status is approved
		# 			if status == 'aeo7' : 
		# 				updateTask = 'anim_splining'
		# 				break

		# 			else : 
		# 				updateTask = 'anim_blocking'
		# 				break

		# 		if taskName == 'anim_splining' : 
		# 			updateTask = taskName
		# 			break

		# 		taskInfo[shotName] = updateTask


		# return taskInfo



	def getServerVersionInfo(self) : 
		# project 
		project = self.getProjectName()
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
		project = self.getProjectName()
		episode = project.split('_')[-1]
		serverPath = '%s/ttv/%s' % (self.mediaPath, episode) 
		publishInfo = dict()
		
		seqs = fileUtils.listFolder(serverPath)

		for eachSeq in seqs : 

			if eachSeq.startswith('sq') : 
				browseShot = '%s/%s' % (serverPath, eachSeq)
				shots = fileUtils.listFolder(browseShot)

				for eachShot in shots : 
					if eachShot.startswith('sh') : 
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


		self.publishInfo = publishInfo
		return publishInfo
		# for each in sorted(publishInfo) : 
		# 	print each, publishInfo[each]




	# button action =======================================================================================

	def doScanShot(self) : 
		self.listData()
		self.resizeColumn()


	def listData(self, mode = 'normal') : 
		row = 0
		height = 20
		widget = 'shotgun_tableWidget'
		shotInfo = dict()
		color = [255, 255, 255]
		color2 = [240, 240, 240]

		self.ui.status_label.setText('Listing shot ...')
		QtGui.QApplication.processEvents()

		shots = self.getSGShotInfo()
		self.ui.status_label.setText('list version ...')
		print 'list version ...'
		shotVersionInfo = self.getSGVersionInfo()
		QtGui.QApplication.processEvents()

		print 'list file server ...'
		self.ui.status_label.setText('list file server ...')
		serverVersionInfo = self.getServerVersionInfo()
		QtGui.QApplication.processEvents()

		print 'list publish version ...'
		self.ui.status_label.setText('list publish version ...')
		publishVersionInfo = self.getPublishVersionInfo()
		QtGui.QApplication.processEvents()

		print 'list task info ...'
		self.ui.status_label.setText('list task info ...')
		taskInfo = self.getSGTaskInfo()
		QtGui.QApplication.processEvents()

		self.ui.status_label.setText('listing data ...')
		print 'listing data ...'
		QtGui.QApplication.processEvents()

		if mode == 'normal' : 
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
			statusColor2 = color
			convertColor = color
			nameColor = color2
			sgTask = '-'
			dep = str()
			movieSg = str()
			step = ''
			publishPath = str()
			statusIcon = str()

			# get update task
			updateTask = self.getUpdateTask(shotName)

			# get version from shotgun
			# if this has a version 
			if shotName in shotVersionInfo.keys() : 
				versionName = shotVersionInfo[shotName]['versionName']
				uploadMovie = shotVersionInfo[shotName]['uploadMovie']
				updateTask = self.getUpdateTask(shotName)
				
				# if uploadMovie in version 
				if uploadMovie : 
					movieSg = True
					if updateTask == 'anim_blocking' or updateTask == 'anim_splining' : 
						dep = 'anim'

					elif updateTask == 'layout' : 
						dep = 'layout'

					else : 
						updateTask = '-'
						movieSg = False

					if dep : 
						# get mov file from server
						if shotName in serverVersionInfo.keys() : 
							# search version that match the dep
							if dep in serverVersionInfo[shotName].keys() : 
								serverMovie = serverVersionInfo[shotName][dep]

							# if dep = layout, try to look for anim
							elif dep == 'layout' : 
								if 'anim' in serverVersionInfo[shotName].keys() : 
									serverMovie = serverVersionInfo[shotName]['anim']
									dep = 'anim'
									# updateTask = self.getUpdateTaskSG(shotName)
									updateTask = 'findTaskSG'


						# get mov file from publish server
						if shotName in publishVersionInfo.keys() : 
							# looking for version that match dep
							if dep in publishVersionInfo[shotName].keys() : 
								publishMovie = publishVersionInfo[shotName][dep]
								path = publishVersionInfo[shotName]['path']
								publishPath = '%s/%s' % (path, publishMovie)

							# if dep = layout, try looking for anim
							elif dep == 'layout' : 
								if 'anim' in serverVersionInfo[shotName].keys() : 
									serverMovie = serverVersionInfo[shotName]['anim']
									dep = 'anim'
									path = publishVersionInfo[shotName]['path']
									publishPath = '%s/%s' % (path, publishMovie)
									# updateTask = self.getUpdateTaskSG(shotName)
									updateTask = 'findTaskSG'

					else : 
						dep = '-'


				else : 
					movieSg = False
					updateTask = '-'

			else : 
				movieSg = False
				updateTask = '-'

			# if server has no movie or no version 
			if not movieSg : 

				# looking in the server
				if shotName in serverVersionInfo.keys() : 
					serverMovieInfo = serverVersionInfo[shotName]

					# looking for anim (the lastest one)
					if 'anim' in serverMovieInfo.keys() : 
						serverMovie = serverMovieInfo['anim']
						dep = 'anim'
						# updateTask = self.getUpdateTaskSG(shotName)
						updateTask = 'findTaskSG'

					elif 'layout' in serverMovieInfo.keys() : 
						serverMovie = serverMovieInfo['layout']
						dep = 'layout'
						updateTask = 'layout'


				# looking in publish server
				if shotName in publishVersionInfo.keys() : 
					publishMovieInfo = publishVersionInfo[shotName]

					# looking for anim 
					if 'anim' in publishMovieInfo.keys() : 
						publishMovie = publishMovieInfo['anim']
						path = publishVersionInfo[shotName]['path']
						publishPath = '%s/%s' % (path, publishMovie)
						dep = 'anim'

					elif 'layout' in publishMovieInfo.keys() : 
						publishMovie = publishMovieInfo['layout']
						path = publishVersionInfo[shotName]['path']
						publishPath = '%s/%s' % (path, publishMovie)
						dep = 'layout'

			# compare shotgun and server version
			serverMovieName = os.path.basename(serverMovie)

			good = None

			# if equal, mean same version 
			if uploadMovie == serverMovieName : 
				if not uploadMovie == '-' : 
					action = 'Good'
					statusColor = self.green
					statusColor2 = self.lightGreen
					nameColor = statusColor
					good = True
					statusIcon = 'ok'

				else : 
					action = '-'
					print 'shotName', shotName

			# looking for other versions
			# see version
			uploadVersion = self.findVersion(uploadMovie)
			serverVersion = self.findVersion(serverMovieName)
			publishVersion = self.findVersion(publishMovie)


			# if both of them return version
			if uploadVersion : 
				if serverVersion and not publishVersion : 

					# if server is newer
					if int(serverVersion) > int(uploadVersion) : 
						action = 'Need upload'
						statusColor = self.orange
						statusColor2 = self.lightOrange
						nameColor = statusColor

						if dep == 'anim' : 
							statusIcon = 'ready'

						if dep == 'layout' : 
							statusIcon = 'needAttention'

					# if shotgun is newer 
					if int(serverVersion) < int(uploadVersion) : 
						action = 'Email coordinator'
						statusColor = self.yellow
						statusColor2 = self.lightYellow
						nameColor = statusColor
						statusIcon = 'needAttention'

				# looking for publish version
				if publishVersion and not serverVersion: 
					if int(publishVersion) == int(uploadVersion) : 
						action = 'Good'
						statusColor = self.green
						statusColor2 = self.lightGreen
						nameColor = statusColor
						statusIcon = 'ok'

					if int(publishVersion) > int(uploadVersion) : 
						action = 'Need upload*'
						statusColor = self.orange
						statusColor2 = self.lightOrange
						convert = 'Yes'
						convertColor = self.green
						nameColor = statusColor
						updateTask = 'findTaskSG'

						if dep == 'anim' : 
							statusIcon = 'ready'

						if dep == 'layout' : 
							statusIcon = 'needAttention'

					elif int(publishVersion) < int(uploadVersion) : 
						action = 'Shotgun newer'
						statusColor = self.yellow
						statusColor2 = self.lightYellow
						nameColor = statusColor
						statusIcon = 'ok'

				if serverVersion and publishVersion : 
					if int(serverVersion) > int(publishVersion) : 
						action = 'Good*2'
						statusColor = self.green
						statusColor2 = self.lightGreen
						nameColor = statusColor
						statusIcon = 'ok'

					if int(serverVersion) < int(publishVersion) : 
						action = 'Need upload*'
						statusColor = self.orange
						statusColor2 = self.lightOrange
						convert = 'Yes'
						convertColor = self.green
						nameColor = statusColor
						updateTask = 'findTaskSG'

						if dep == 'anim' : 
							statusIcon = 'ready'

						if dep == 'layout' : 
							statusIcon = 'needAttention'

				# no publish version
				else : 
					action = 'Good*2'
					statusColor = self.green
					statusColor2 = self.lightGreen
					nameColor = statusColor
					statusIcon = 'ok'

			else : 
				if serverVersion and not publishVersion : 
					action = 'Need upload'
					statusColor = self.orange
					statusColor2 = self.lightOrange
					nameColor = statusColor

					if dep == 'anim' : 
						statusIcon = 'ready'

					if dep == 'layout' : 
						statusIcon = 'needAttention'

				if publishVersion and not serverVersion : 
					action = 'Need upload*'
					statusColor = self.orange
					statusColor2 = self.lightOrange
					nameColor = statusColor
					convert = 'Yes'
					convertColor = self.green
					updateTask = 'findTaskSG'

					if dep == 'anim' : 
						statusIcon = 'ready'

					if dep == 'layout' : 
						statusIcon = 'needAttention'

				if publishVersion and serverVersion : 
					if int(serverVersion) > int(publishVersion) : 
						action = 'Good*2'
						statusColor = self.green
						statusColor2 = self.lightGreen
						nameColor = statusColor
						statusIcon = 'ok'


					if int(serverVersion) < int(publishVersion) : 
						action = 'Need upload*'
						statusColor = self.orange
						statusColor2 = self.lightOrange
						convert = 'Yes'
						convertColor = self.green
						nameColor = statusColor
						updateTask = 'findTaskSG'

						if dep == 'anim' : 
							statusIcon = 'ready'

						if dep == 'layout' : 
							statusIcon = 'needAttention'


					else : 
						action = 'Need upload'
						statusColor = self.orange
						statusColor2 = self.lightOrange
						nameColor = statusColor

						if dep == 'anim' : 
							statusIcon = 'ready'

						if dep == 'layout' : 
							statusIcon = 'needAttention'


				if not uploadMovie == '-' : 
					action = 'SG wrong naming'
					statusColor = self.red
					statusColor2 = self.lightRed
					nameColor = statusColor
					statusIcon = 'needAttention'


			datas = {	
						'status': {'text': status, 'icon': statusIcon, 'color': statusColor2},
						'shotName': {'text': shotName, 'color': nameColor},
						'uploadMovie': {'text': uploadMovie, 'color': statusColor2},
						'serverMovie': {'text': serverMovieName, 'color': statusColor2},
						'publishMovie': {'text': publishMovie, 'color': statusColor2},
						'convert': {'text': convert, 'color': convertColor},
						'action': {'text': action, 'color': statusColor2},
						'step': {'text': dep, 'color': statusColor2},
						'task': {'text': updateTask, 'color': statusColor2}
					}

			keywords = []
			filter1 = 'anim'
			filter2 = 'layout'
			filter3 = 'comp'
			noFilter = '-'

			anim = self.ui.anim_checkBox.isChecked()
			layout = self.ui.layout_checkBox.isChecked()
			comp = self.ui.comp_checkBox.isChecked()

			if anim : 
				keywords.append(filter1)

			if layout : 
				keywords.append(filter2)

			if comp : 
				keywords.append(filter3)

			if not keywords : 
				keywords = [dep]

			if dep in keywords : 
				self.fillData(row, datas, mode)
				self.allInfo[shotName] = {'serverMovie': serverMovie, 'publishMovie': publishPath}
				# self.allInfo[shotName].update(datas)

				row += 1


		self.ui.status_label.setText('')
		QtGui.QApplication.processEvents()


	def doUpdate(self) : 
		
		widget = 'shotgun_tableWidget'
		i = 0
		row = 0
		allItem = self.ui.all_checkBox.isChecked()

		# selection
		if not allItem : 
			selRow = self.getSelectionRows(widget)
			
			if selRow : 
				topRow = selRow[0]

				# get data from table
				actions = self.getDataFromSelectedRange(self.actionColumn, widget)
				shots = self.getDataFromSelectedRange(self.shotColumn, widget)
				serverFiles = self.getDataFromSelectedRange(self.serverColumn, widget)
				publishFiles = self.getDataFromSelectedRange(self.publishColumn, widget)
				steps = self.getDataFromSelectedRange(self.stepColumn, widget)
				tasks = self.getDataFromSelectedRange(self.taskColumn, widget)
				converts = self.getDataFromSelectedRange(self.convertColumn, widget)

				row = topRow

			else : 
				self.completeDialog('Error', 'Selecte atlease one item')

		else : 
			actions = self.getAllData(self.actionColumn, widget)
			shots = self.getAllData(self.shotColumn, widget)
			serverFiles = self.getAllData(self.serverColumn, widget)
			publishFiles = self.getAllData(self.publishColumn, widget)
			steps = self.getAllData(self.stepColumn, widget)
			tasks = self.getAllData(self.taskColumn, widget)
			converts = self.getAllData(self.convertColumn, widget)


		

		for action in actions : 
			shotName = shots[i]
			serverFile = serverFiles[i]
			publishFile = publishFiles[i]
			task = tasks[i]
			convert = converts[i]

			# if shotName in self.serverShotInfo.keys() : 
			# 	self.serverShotInfo[shotName]

			step = steps[i]

			if action == 'Need upload' : 
				if step == 'anim' : 
					try : 
						self.setStatus(row, 'ip', True)
						self.updateSG(shotName, serverFile, task, 'serverMovie')
						self.listData('refresh')

					except Exception as error : 
						print error
						self.setStatus(row, 'x', True)

				if step == 'layout' : 
					if not allItem : 
						self.completeDialog('Warning', 'Skip update layout')

			if action == 'Need upload*' : 
				if step == 'anim' : 
					self.setStatus(row, 'convert', True)
					convertFile = self.convertMov(shotName)

					if convertFile : 
						self.setStatus(row, 'ip', True)
						self.updateSG(shotName, convertFile, task, 'publishMovie')
						self.listData('refresh')

					else : 
						print 'No file'

					# if step == 'layout' : 
					# 	self.completeDialog('Warning', 'Skip update layout')

			# else : 
			# 	if not allItem : 
			# 		self.completeDialog('Error', 'No data for this shot')

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
				updateTask = 'layout'

		# if no version, looking in the server what latest version
		else : 
			updateTask = None

		return updateTask



	def getUpdateTaskSG(self, shotName) : 
		projectName = self.getProjectName()
		updateTask = None

		filters = [['project.Project.name', 'is', projectName], ['entity.Shot.code', 'is', shotName]]    
		fields = ['content', 'id', 'sg_status_list']
		tasks = sgUtils.sg.find('Task', filters, fields)

		for eachTask in tasks : 
			taskName = eachTask['content']
			status = eachTask['sg_status_list']
			
			# if task is blocking
			if taskName == 'anim_blocking' : 
				# if status is approved
				if status == 'aeo7' : 
					updateTask = 'anim_splining'
					break

				else : 
					updateTask = 'anim_blocking'
					break

			if taskName == 'anim_splining' : 
				updateTask = taskName
				break


		return updateTask


	def updateSG(self, shotName, movieFile, task, movieType) : 

		taskID = None
		shotID = None
		setTaskStatus = 'rev'
		versionName = os.path.basename(movieFile).replace('.mov', '')
		projectName = self.getProjectName()

		if task == 'findTaskSG' : 
			task = self.getUpdateTaskSG(shotName)

		if shotName in self.allInfo.keys() : 
			if movieType == 'serverMovie' : 
				movieFile = self.allInfo[shotName]['serverMovie']

			if movieType == 'publishMovie' : 
				movieFile = movieFile

			movieFile = movieFile.replace('/', '\\')

			# if shotName has version, get taskID, shotID from version data
			if shotName in self.shotVersionInfo.keys() : 
				versionInfo = self.shotVersionInfo[shotName]
				shotInfo = versionInfo['shotID']
				taskStatus = versionInfo['taskStatus']

				result = self.findTaskID(projectName, shotName, task)

				if result : 
					taskID = result[0]['id']

				if shotInfo : 
					shotID = shotInfo['id']


				self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)


			# no version data, get shotID and taskID by calling shotgun
			else : 
				if shotName in self.shotInfo.keys() : 

					shotID = self.shotInfo[shotName]['id']
					result = self.findTaskID(projectName, shotName, task)

					if result : 
						taskID = result[0]['id']
						self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)

					else : 
						self.completeDialog('Error', 'Cannot find task ID')


	def updateSGCmd(self, projectName, versionName, shotID, taskID, movieFile, status) : 
		print 'versionName', versionName
		print 'shotID', shotID
		print 'taskID', taskID
		print 'movieFile', movieFile
		print 'status', status

		proj = sgUtils.sg.find_one('Project', [['name', 'is', projectName]])

		data = { 'project': proj,
				 'code': versionName,
				 'entity': {'type':'Shot', 'id':shotID},
				 'sg_task': {'type':'Task', 'id':taskID},
				 'sg_status_list': status, 
				 # 'sg_path': {'local_path': publishFile, 'name': version}

			 }	

		self.ui.status_label.setText('Creating version ...')
		result = sgUtils.sg.create('Version', data)
		print 'Create version %s success' % versionName
		QtGui.QApplication.processEvents()

		self.ui.status_label.setText('Uploading movie ...')
		print 'Uploading movie ...'
		result2 = sgUtils.sg.upload('Version', result['id'], movieFile.replace('/', '\\'), 'sg_uploaded_movie')
		print 'Upload movie %s success' % movieFile
		print '=================================='
		QtGui.QApplication.processEvents()

		return result2


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


	def fillData(self, row, datas, mode = 'normal') : 
		# normal = insertRow
		# refresh = not insertRow

		status = datas['status']['text']
		statusIcon = datas['status']['icon']
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
		if mode == 'normal' : 
			self.insertRow(row, height, widget)

		self.setStatus(row, statusIcon)
		# self.fillInTable(row, self.statusColumn, status, widget, statusColor)
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
		# self.ui.shotgun_tableWidget.setColumnHidden(self.publishColumn, True)
		# self.ui.shotgun_tableWidget.setColumnHidden(self.stepColumn, True)
		# self.ui.shotgun_tableWidget.setColumnHidden(self.taskColumn, True)
		# self.ui.shotgun_tableWidget.setColumnHidden(self.convertColumn, True)



	def setLogo(self) : 
		# set company logo
		path = os.path.dirname(moduleDir)
		iconPath = '%s/icons/%s' % (path, self.logo)

		self.ui.logo_label.setPixmap(QtGui.QPixmap(iconPath).scaled(200, 40, QtCore.Qt.KeepAspectRatio))


	def setStatus(self, row, status, update = False) : 

		column = self.statusColumn
		text = ''
		widget = 'shotgun_tableWidget'
		iconPath = str()

		if status == 'ok' : 
			iconPath = '%s/icons/%s' % (self.iconDir, self.okIcon)

		if status == 'ready' : 
			iconPath = '%s/icons/%s' % (self.iconDir, self.readyIcon)

		if status == 'x' : 
			iconPath = '%s/icons/%s' % (self.iconDir, self.xIcon)

		if status == 'ip' : 
			iconPath = '%s/icons/%s' % (self.iconDir, self.ipIcon)

		if status == 'needAttention' : 
			iconPath = '%s/icons/%s' % (self.iconDir, self.needAttention)

		if status == 'convert' : 
			iconPath = '%s/icons/%s' % (self.iconDir, self.convertIcon)

		iconPath = iconPath.replace('/', '\\')

		self.fillInTableIcon(row, column, text, iconPath, widget, [255, 255, 255])

		if update : 
			QtGui.QApplication.processEvents()


	# general function =======================================================================

	def findVersion(self, inputFile) : 
		eles = inputFile.split('.')
		version = None

		for each in eles : 
			if each[0] == 'v' and each[1:].isdigit() : 
				version = each[1:]

		return version


	def getProjectName(self) : 
		projectName = str(self.ui.project_comboBox.currentText())
		projectName = 'ttv_e100'

		return projectName

	# table part ==========================================================================================

	def insertRow(self, row, height, widget) : 
		cmd1 = 'self.ui.%s.insertRow(row)' % widget
		cmd2 = 'self.ui.%s.setRowHeight(row, height)' % widget

		eval(cmd1)
		eval(cmd2)


	def fillInTable(self, row, column, text, widget, color = [1, 1, 1]) : 
		item = QtGui.QTableWidgetItem()
		item.setText(text)
		item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
		cmd = 'self.ui.%s.setItem(row, column, item)' % widget
		eval(cmd)


	def fillInTableIcon(self, row, column, text, iconPath, widget, color = [1, 1, 1]) : 
		icon = QtGui.QIcon()
		icon.addPixmap(QtGui.QPixmap(iconPath), QtGui.QIcon.Normal, QtGui.QIcon.Off)

		item = QtGui.QTableWidgetItem()
		item.setText(str(text))
		item.setIcon(icon)
		item.setBackground(QtGui.QColor(color[0], color[1], color[2]))
		
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



	# convertion part ===========================================================================


	def convertMov(self, shotName) : 
		project = self.getProjectName()
		episode = project.split('_')[-1]
		serverPath = '%s/ttv/%s/shotgun' % (self.mediaPath, episode) 
		inputFile = self.allInfo[shotName]['publishMovie']
		fileName = os.path.basename(inputFile)
		outputFile = '%s/%s' % (serverPath, fileName)

		print inputFile, outputFile

		if not os.path.exists(outputFile) : 
			self.convertCmd(inputFile, outputFile, self.frameRate)

			if os.path.exists(outputFile) : 
				return outputFile

		else : 
			print 'file exists -> skip'



	def convertCmd(self, inputFile, outputFile, frameRate) : 
		convertorPath = 'U:/applications/ffmpeg/win/ffmpeg.exe'
		src = inputFile.replace('/', '\\')
		dst = outputFile.replace('/', '\\')
		cmd = '"%s" -y -i %s -r %s -vcodec libx264 -vprofile baseline -crf 22 -bf 0 -pix_fmt yuv420p -f mov %s' % (convertorPath.replace('/', '\\'), src, frameRate, dst)

		os.system(cmd)



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = MyForm()
    myapp.show()
    sys.exit(app.exec_())