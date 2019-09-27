import requests

class SnipsRobonect:
	def __init__(self, ipaddress, username, password):
		self.ip = ipaddress
		self.username = username
		self.password = password

	def getUrl(self):
		return "http://%s/json" % (self.ip)

	def getStatus(self):
		r = requests.get(self.getUrl() + "?cmd=status", auth=(self.username, self.password))
		if r.status_code == 200:
			return r.json()
		else:
			print("Failed to get status, error: %s" % r.status_code)
			return False

	# def setMode(self, mode):
		r = requests.get(self.getUrl() + "?cmd=mode&mode=%s" % mode, auth=(self.username, self.password))
		if r.status_code == 200:
			return True
		else:
			print("Failed to set mode, error: %s" % r.status_code)
			return False

	def startJob(self, startTime, duration):
		r = requests.get(self.getUrl() + "?cmd=mode&mode=job&startTime=%s&duration=%s" % (startTime, duration), auth=(self.username, self.password))
		if r.status_code == 200:
			return True
		else:
			print("Failed to start job, error: %s" % r.status_code)
			return False

	def endDay(self):
		return self.setMode("eod")

	def start(self):
		r = requests.get(self.getUrl() + "?cmd=start", auth=(self.username, self.password))
		if r.status_code == 200:
			return True
		else:
			print("Failed to start")
			return False

	def stop(self):
		r = requests.get(self.getUrl() + "?cmd=stop", auth=(self.username, self.password))

		if r.status_code == 200:
			return True
		else:
			print("Failed to stop")
			return False