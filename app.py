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

from arxShotgunVersionCheck import ui3 as ui
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
		self.actionList = []

		self.serverVersionInfo = dict()
		self.publishVersionInfo = dict()
		self.sgVersionInfo = dict()

		self.task = {'anim': ['anim_splining', 'anim_blocking'], 'comp': ['compositing'], 'layout': []}


		self.initFunctions()
		self.initConnections()



	def initFunctions(self) : 
		self.setLogo()
		self.listProjects()
		self.listFilter()
		self.resizeColumn()



	def initConnections(self) : 
		self.ui.getData_pushButton.clicked.connect(self.doScanShot)
		self.ui.update_pushButton.clicked.connect(self.doUpdate)
		self.ui.showAll_checkBox.stateChanged.connect(self.refreshUI)
		self.ui.layout_radioButton.toggled.connect(self.refreshUI)
		self.ui.anim_radioButton.toggled.connect(self.refreshUI)
		self.ui.composite_radioButton.toggled.connect(self.refreshUI)
		self.ui.filter_comboBox.currentIndexChanged.connect(self.refreshUI)
		self.ui.all_checkBox.stateChanged.connect(self.setButtonUI)



	def listProjects(self) : 
		# sg command
		projects = sgUtils.sg.find('Project', filters=[], fields=['name'])

		self.ui.project_comboBox.clear()
		projectList = []

		for eachProject in sorted(projects) : 
			projectName = eachProject['name']
			projectList.append(projectName)

		for eachProject in sorted(projectList) :
			self.ui.project_comboBox.addItem(eachProject)



	def listFilter(self) : 
		self.ui.filter_comboBox.clear()
		self.ui.filter_comboBox.addItem('All actions')


	def setFilterComboBox(self) : 
		currentItem = str(self.ui.filter_comboBox.currentText())
		self.ui.filter_comboBox.currentIndexChanged.disconnect(self.refreshUI)
		self.ui.filter_comboBox.clear()
		self.ui.filter_comboBox.addItem('All actions')
		i = 0
		index = 0

		for each in sorted(self.actionList) : 
			self.ui.filter_comboBox.addItem(each)

			if currentItem == each : 
				index = i + 1

			i += 1

		self.ui.filter_comboBox.setCurrentIndex(index)
		self.ui.filter_comboBox.currentIndexChanged.connect(self.refreshUI)



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

			# version that linked to shot
			if entity : 
				shotName = entity['name']

				# version that has movie
				if uploadMovie : 
					uploadMovie = eachVersion['sg_uploaded_movie']['name']
					currentVer = self.findVersion(uploadMovie)

					# find department 
					# if version has linked to task 
					if taskID : 
						taskName = taskID['name']

						''' define department by task and name '''
						for eachDep in self.task : 
							step = eachDep 
							tasks = self.task[step]


							# if task name in valid list
							if taskName in tasks : 
								tmpDict = {'versionName': versionName, 'versionId': eachVersion['id'], 'uploadMovie': uploadMovie, 'shotID': shotID, 'taskID': taskID, 'taskStatus': taskStatus}

								# if not step in data
								if not shotName in shotVersionInfo.keys() : 
									shotVersionInfo[shotName] = {step: tmpDict}


								# if step already in data, check if it has a higher version
								else : 
									if not step in shotVersionInfo[shotName].keys() : 
										shotVersionInfo[shotName].update({step: tmpDict})

									else : 
										previousVersion = shotVersionInfo[shotName][step]['versionName']
										previousVersionNumber = self.findVersion(previousVersion)

										# yes, add to step
										if currentVer > previousVersionNumber : 
											shotVersionInfo[shotName][step] = tmpDict  

					# if no task name 
					else : 
						# assume that version is layout
						step = 'layout'
						tmpDict = {'versionName': versionName, 'versionId': eachVersion['id'], 'uploadMovie': uploadMovie, 'shotID': shotID, 'taskID': taskID, 'taskStatus': taskStatus}

						if step in versionName : 
							if not shotName in shotVersionInfo.keys() : 
								shotVersionInfo[shotName] = {step: tmpDict}

							else : 
								if not step in shotVersionInfo[shotName].keys() : 
									shotVersionInfo[shotName].update({step: tmpDict})

								else : 
									previousVersion = shotVersionInfo[shotName][step]['versionName']
									previousVersionNumber = self.findVersion(previousVersion)

									# yes, add to step
									if currentVer > previousVersionNumber : 
										shotVersionInfo[shotName][step] = tmpDict  


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

							# loop each file in each department
							for eachFile in files : 

								dep = eachFile.split('_')[-1].split('.')[0]
								fullPathFile = '%s/%s' % (browseFile, eachFile)

								# confirm correct naming by match department name and file name
								if eachDep == dep : 
									version = self.findVersion(eachFile)
									
									if version > max : 
										maxVersion = fullPathFile

							if maxVersion : 
								shotName = ('_').join(maxVersion.split('_')[1:4])

								if not shotName in publishInfo.keys() : 
									publishInfo[shotName] = {dep: maxVersion}

								else : 
									if not dep in publishInfo[shotName].keys() : 
										publishInfo[shotName].update({dep: maxVersion})


		self.publishInfo = publishInfo
		return publishInfo
		# for each in sorted(publishInfo) : 
		# 	print each, publishInfo[each]

	def getServerFile(self, shotName, dep) : 

		serverFile = str()
		publishFile = str()
		convert = False
		returnData = []

		# if server has file
		if shotName in self.serverVersionInfo.keys() : 
			if dep in self.serverVersionInfo[shotName].keys() : 
				serverFile = self.serverVersionInfo[shotName][dep]


		if shotName in self.publishVersionInfo.keys() : 
			if dep in self.publishVersionInfo[shotName].keys() : 
				publishFile = self.publishVersionInfo[shotName][dep]

		if serverFile and publishFile : 
			serverVersion = self.findVersion(serverFile)
			publishVersion = self.findVersion(publishFile)

			if serverVersion > publishVersion : 
				convert = False
				heroFile = serverFile
				returnData = [heroFile, convert, serverFile, publishFile]

			if serverVersion < publishVersion : 
				convert = True 
				heroFile = publishFile
				returnData = [heroFile, convert, serverFile, publishFile]

			if serverVersion == publishVersion : 
				convert = False
				heroFile = serverFile
				returnData = [heroFile, convert, serverFile, publishFile]

		elif serverFile : 
			convert = False
			heroFile = serverFile
			publishFile = '-'
			returnData = [heroFile, convert, serverFile, publishFile]


		elif publishFile : 
			convert = True
			heroFile = publishFile 
			serverFile = '-'
			returnData = [heroFile, convert, serverFile, publishFile]


		return returnData



	def getSGUploadFile(self, shotName, dep) : 

		if shotName in self.sgVersionInfo.keys() : 
			if dep in self.sgVersionInfo[shotName].keys() : 
				versionInfo = self.sgVersionInfo[shotName][dep]
				uploadMovie = versionInfo['uploadMovie']

				if uploadMovie : 
					return uploadMovie



	# button action =======================================================================================

	def doScanShot(self, mode = 'normal') : 
		self.setStatusLine('Listing data ...')
		self.shots = self.getSGShotInfo()
		self.serverVersionInfo = self.getServerVersionInfo()
		self.publishVersionInfo = self.getPublishVersionInfo()
		self.sgVersionInfo = self.getSGVersionInfo()
		self.listData(mode)
		self.setFilterComboBox()
		self.resizeColumn()


	def refreshUI(self) : 
		self.listData ('normal')
		self.resizeColumn()


	def setButtonUI(self) : 
		state = self.ui.all_checkBox.isChecked()

		if state : 
			self.ui.update_pushButton.setText('Update All Shot')

		else : 
			self.ui.update_pushButton.setText('Update Selected Shot')

	
	def refreshData(self, filters = None) : 
		self.setStatusLine('Refreshing data ...')
		self.shots = self.getSGShotInfo()
		self.serverVersionInfo = self.getServerVersionInfo()
		self.publishVersionInfo = self.getPublishVersionInfo()
		self.sgVersionInfo = self.getSGVersionInfo()
		self.listData('refresh', filters)
		self.resizeColumn()



	def listData(self, mode, filters = None) : 

		row = 0
		height = 20
		widget = 'shotgun_tableWidget'
		shotInfo = dict()
		color = [255, 255, 255]
		color2 = [240, 240, 240]

		if mode == 'normal' : 
			self.clearTable(widget)

		# self.writeLog(str(shotVersionInfo))


		for eachShot in sorted(self.shots) : 
			status = '-'
			shotName = eachShot['code']
			versionName = '-'
			uploadMovie = '-'
			serverMovie = '-'
			publishMovie = '-'
			serverMovieName = '-'
			convert = '-'
			dep = str()
			action = '-'
			updateTask = '-'
			statusColor = color
			statusColor2 = color
			convertColor = color
			nameColor = color2
			depFilter = self.getDepartment()
			statusIcon = self.okIcon
			heroFile = str()
			sgMovieVersion = str()
			serverVersion = str()
			showShot = False

			# check if this shot is in shotgun
			sgMovie = self.getSGUploadFile(shotName, depFilter)
			serverFileInfo = self.getServerFile(shotName, depFilter)

			if sgMovie : 
				uploadMovie = os.path.basename(sgMovie)
				sgMovieVersion = self.findVersion(uploadMovie)
				dep = depFilter

				if uploadMovie and not sgMovieVersion : 
					action = 'Wrong naming'

			if serverFileInfo : 
				heroFile = serverFileInfo[0]
				convert = serverFileInfo[1]
				serverFile = serverFileInfo[2]
				publishFile = serverFileInfo[3]
				serverMovie = os.path.basename(serverFile)
				publishMovie = os.path.basename(publishFile)
				dep = depFilter

				serverVersion = self.findVersion(os.path.basename(heroFile))

				if convert : 
					convert = 'Yes'

				else : 
					convert = '-'


			# compare condition
			# if shotgun and serverFile available
			if sgMovieVersion and serverVersion : 
				if sgMovieVersion < serverVersion : 
					action = 'Need upload'					

				if sgMovieVersion == serverVersion : 
					action = 'Good'					

				if sgMovieVersion > serverVersion : 
					action = 'Email Coordinator'					

			# if only shotgun file available
			elif sgMovieVersion : 
				action = 'Good'				

			# if only serverFile available
			elif serverVersion : 
				action = 'Need upload'		


			# define color ===============================================================
			if action == 'Good' : 
				statusColor2 = self.lightGreen	
				nameColor = self.green
				statusIcon = 'ok'

			elif action == 'Need upload' : 
				statusColor2 = self.lightOrange
				nameColor = self.orange
				statusIcon = 'ready'

			elif action == 'Email Coordinator' : 
				statusColor2 = self.lightYellow
				nameColor = self.yellow
				statusIcon = 'needAttention'

			elif action == 'Wrong naming' : 
				statusColor2 = self.lightYellow
				nameColor = self.yellow
				statusIcon = 'needAttention'

			if convert == 'Yes' : 
				convertColor = self.lightGreen


			# collect action
			if not action in self.actionList : 
				self.actionList.append(action)



			datas = {	
						'status': {'text': status, 'icon': statusIcon, 'color': statusColor2},
						'shotName': {'text': shotName, 'color': nameColor},
						'uploadMovie': {'text': uploadMovie, 'color': statusColor2},
						'serverMovie': {'text': serverMovie, 'color': statusColor2},
						'publishMovie': {'text': publishMovie, 'color': statusColor2},
						'convert': {'text': convert, 'color': convertColor},
						'action': {'text': action, 'color': statusColor2},
						'step': {'text': dep, 'color': statusColor2},
						'task': {'text': updateTask, 'color': statusColor2}
					}

			
			
			# filter area =========================================================

			if self.ui.showAll_checkBox.isChecked() : 
				showShot = True

			else : 
				if not action == '-' : 
					showShot = True

				else : 
					showShot = False

			currentFilter = str(self.ui.filter_comboBox.currentText())
			if not currentFilter == 'All actions' : 
				if currentFilter == action : 
					showShot = True

				else : 
					showShot = False

			if filters : 
				if shotName in filters : 
					showShot = True

				else : 
					showShot = False


			if showShot : 
				self.fillData(row, datas, mode)
				self.allInfo[shotName] = {'serverMovie': serverFile, 'publishMovie': publishFile}

				row += 1


		self.setStatusLine('')



	def doUpdate(self) : 
		
		currentFilter = self.ui.filter_comboBox.currentText()
		widget = 'shotgun_tableWidget'
		i = 0
		row = 0
		allItem = self.ui.all_checkBox.isChecked()
		shotFilters = self.getAllData(self.shotColumn, widget)

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

			# if step == 'anim' : 
			if action == 'Need upload' and convert == 'Yes' : 

				self.setStatus(row, 'convert', True)
				convertFile = self.convertMov(shotName)

				if convertFile : 
					self.setStatus(row, 'ip', True)
					self.updateSG(shotName, step, convertFile)
					self.refreshData(shotFilters)

			elif action == 'Need upload' : 
				try : 
					self.setStatus(row, 'ip', True)
					serverFile = self.allInfo[shotName]['serverMovie']
					self.updateSG(shotName, step, serverFile)
					self.refreshData(shotFilters)

				except Exception as error : 
					print error
					self.setStatus(row, 'x', True)


			row += 1
			i += 1


		self.completeDialog('Complete', 'Update success')


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


	def updateSG(self, shotName, step, movieFile) : 

		taskID = None
		shotID = None
		version = True
		setTaskStatus = 'rev'
		versionName = os.path.basename(movieFile).replace('.mov', '')
		projectName = self.getProjectName()

		if step == 'anim' : 
			task = self.getUpdateTaskSG(shotName)

		if step == 'layout' : 
			task = None

		if step == 'comp' : 
			task = 'compositing'

		movieFile = movieFile.replace('/', '\\')

		# if shotName has version, get taskID, shotID from version data
		if shotName in self.shotVersionInfo.keys() : 
			if step in self.shotVersionInfo[shotName].keys() : 
				versionInfo = self.shotVersionInfo[shotName][step]
				shotInfo = versionInfo['shotID']
				taskStatus = versionInfo['taskStatus']

				if step == 'anim' or step == 'comp' : 

					result = self.findTaskID(projectName, shotName, task)

					if result : 
						taskID = result[0]['id']

					if shotInfo : 
						shotID = shotInfo['id']


					self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)

				if step == 'layout' : 

					if shotInfo : 
						shotID = shotInfo['id']

					taskID = None
					self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)



			else : 
				version = False

		else : 
			version = False



		# no version data, get shotID and taskID by calling shotgun
		if not version : 
			if shotName in self.shotInfo.keys() : 
				shotID = self.shotInfo[shotName]['id']

				result = self.findTaskID(projectName, shotName, task)

				if result : 
					taskID = result[0]['id']

				else : 
					taskID = None
				
				self.updateSGCmd(projectName, versionName, shotID, taskID, movieFile, setTaskStatus)



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
				 'sg_status_list': status, 

			 }	

		if taskID : 
			data.update({'sg_task': {'type':'Task', 'id':taskID}})

		self.setStatusLine('Creating version ...')
		result = sgUtils.sg.create('Version', data)
		print 'Create version %s success' % versionName

		self.setStatusLine('Uploading movie ...')
		print 'Uploading movie ...'
		result2 = sgUtils.sg.upload('Version', result['id'], movieFile.replace('/', '\\'), 'sg_uploaded_movie')
		print 'Upload movie %s success' % movieFile
		print '=================================='

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

	def getDepartment(self) : 

		dep = str()
		if self.ui.anim_radioButton.isChecked() : 
			dep = 'anim'

		if self.ui.layout_radioButton.isChecked() : 
			dep = 'layout'

		if self.ui.composite_radioButton.isChecked() : 
			dep = 'comp'

		return dep



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



	def setStatusLine(self, text) : 
		self.ui.status_label.setText(text)
		QtGui.QApplication.processEvents()


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