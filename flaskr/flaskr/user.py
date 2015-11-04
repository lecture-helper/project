class User():
	def __init__(self, username, type = None):
		self.username = username
		self.isStudent = self.isProfessor = False
		if type == 0:
			self.isStudent = True
		else:
			self.isProfessor = True

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return unicode(self.username)