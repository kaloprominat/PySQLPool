"""
@author: Nick Verbeck
@since: 5/12/2008
"""
import pymysql
import datetime
from threading import Semaphore

try:
	from hashlib import md5 
except Exception, e:
	from md5 import md5

class Connection(object):
	"""
	Command Pattern Object to store connection information for use in PySQLPool
	
	@author: Nick Verbeck
	@since: 5/12/2008
	@version: 0.1
	"""
	
	def __init__(self, *args, **kargs):
		"""
		Constructor for the Connection class
		@param commitOnEnd: Default False, When query is complete do you wish to auto commit. This is a always on for this connection
		@author: Nick Verbeck
		@since: 5/12/2008
		@updated: 7/19/2008 - Added commitOnEnd
		@updated: 10/26/2008 - Switched to use *args and **kargs
		"""
		self.info = {
					 'host': 'localhost',
					 'user': 'root',
					 'passwd': '',
					 'db': '',
					 'port': 3306
					 }
		if kargs.has_key('dbhost'):
			self.info['host'] = kargs['dbhost']
		if kargs.has_key('dblogin'):
			self.info['user'] = kargs['dblogin']
		if kargs.has_key('dbpass'):
			self.info['passwd'] = kargs['dbpass']
		if kargs.has_key('dbname'):
			self.info['db'] = kargs['dbname']
		if kargs.has_key('dbport'):
			self.info['port'] = int(kargs['dbport'])
		if kargs.has_key('connect_timeout'):
			self.info['connect_timeout'] = kargs['connect_timeout']
		if kargs.has_key('use_unicode'):
			self.info['use_unicode'] = kargs['use_unicode']
		if kargs.has_key('charset'):
			self.info['charset'] = kargs['charset']
		if kargs.has_key('local_infile'):
			self.info['local_infile'] = kargs['local_infile']
			
		#Support Legacy Username
		if kargs.has_key('username'):
			self.info['user'] = kargs['username']
		#Support Legacy Password
		if kargs.has_key('password'):
			self.info['passwd'] = kargs['password']
		#Support Legacy Schema
		if kargs.has_key('schema'):
			self.info['db'] = kargs['schema']
			
		if kargs.has_key('commitOnEnd'):
			self.commitOnEnd = kargs['commitOnEnd']
		else:
			self.commitOnEnd = False
			
		hashStr = ''.join([str(x) for x in self.info.values()])
		self.key = md5(hashStr).hexdigest()
		
	def __getattr__(self, name):
		try:
			return self.info[name]
		except Exception, e:
			return None
		
	def getKey(self):
		return self.key

connection_timeout = datetime.timedelta(seconds=20)

class ConnectionManager(object):
	"""
	Physical Connection manager
	
	Used to manage the physical MySQL connection and the thread safe locks on that connection
	
	@author: Nick Verbeck
	@since: 5/12/2008
	@version: 0.1
	"""
	def __init__(self, connectionInfo):
		"""
		Constructor for ConnectionManager
		
		@param connectionInfo: Connection Object representing your connection string
		@author: Nick Verbeck
		@since: 5/12/2008
		"""
		
		self.connectionInfo = connectionInfo
		self.connection = None
		
		#Lock management
		self._lock = Semaphore()
		self._locked = False
		
		self.activeConnections = 0
		self.query = None
		self.lastConnectionCheck = None
		
	def lock(self, block=True):
		"""
		Lock connection from being used else where
		"""
		self._locked = True
		return self._lock.acquire(block)
		
	def release(self):
		"""
		Release the connection lock
		"""
		if self._locked is True:
			self._locked = False
			self._lock.release()
		
	def is_locked(self):
		"""
		Returns the status of this connection
		"""
		return self._locked
	
	def getCursor(self):
		"""
		Get a Dictionary Cursor for executing queries
		"""
		if self.connection is None:
			self.Connect()
			
		return self.connection.cursor(pymysql.cursors.DictCursor)
		
	def _updateCheckTime(self):
		"""
		Updates the connection check timestamp
		"""
		self.lastConnectionCheck = datetime.datetime.now()

	def Connect(self):
		"""
		Creates a new physical connection to the database
		
		@author: Nick Verbeck
		@since: 5/12/2008
		"""
		if self.connection is None:
			self.connection = pymysql.connect(*[], **self.connectionInfo.info)
			
		if self.connectionInfo.commitOnEnd is True:
			self.connection.autocommit()
			
		self._updateCheckTime()
		
	def autoCommit(self, autocommit):
		self.connectionInfo.commitOnEnd = autocommit
		if autocommit is True and self.connection is not None:
			self.connection.autocommit()
		
	def ReConnect(self):
		"""
		Attempts to close current connection if open and re-opens a new connection to the database
		
		@author: Nick Verbeck
		@since: 5/12/2008
		"""
		self.Close()
		self.Connect()
		
	def TestConnection(self, forceCheck = False):
		"""
		Tests the current physical connection if it is open and hasn't timed out
		
		@return: boolean True is connection is open, False if connection is closed
		@author: Nick Verbeck
		@since: 5/12/2008
		"""
		if self.connection is None:
			return False
		elif forceCheck is True or (datetime.datetime.now() - self.lastConnectionCheck) >= connection_timeout:
			try:
				#TODO: Find a better way to test if connection is open
				cursor = self.connection.cursor(pymysql.cursors.DictCursor)
				cursor.execute('select current_user')
				self._updateCheckTime()
				return True
			except Exception, e:
				self.connection.close()
				self.connection = None
				return False
		else:
			return True
		
	def being(self):
		"""
		Being a Transaction
		
		@author: Nick Verbeck
		@since: 5/14/2011
		"""
		try:
			if self.connection is not None:
				self.lock()
				c = self.getCursor()
				c.execute('BEGIN;')
				c.close()
		except Exception, e:
			pass
				
			
	def commit(self):
		"""
		Commit MySQL Transaction to database.
		MySQLDB: If the database and the tables support transactions, 
		this commits the current transaction; otherwise 
		this method successfully does nothing.
		
		@author: Nick Verbeck
		@since: 5/12/2008
		"""
		try:
			if self.connection is not None:
				self.connection.commit()
				self._updateCheckTime()
				self.release()
		except Exception, e:
			pass
	Commit = commit
			
	def rollback(self):
		"""
		Rollback MySQL Transaction to database.
		MySQLDB: If the database and tables support transactions, this rolls 
		back (cancels) the current transaction; otherwise a 
		NotSupportedError is raised.
		
		@author: Nick Verbeck
		@since: 5/12/2008
		"""
		try:
			if self.connection is not None:
				self.connection.rollback()
				self._updateCheckTime()
				self.release()
		except Exception, e:
			pass
	
	def Close(self):
		"""
		Commits and closes the current connection
		
		@author: Nick Verbeck
		@since: 5/12/2008
		"""
		if self.connection is not None:
			try:
				self.connection.commit()
				self.connection.close()
				self.connection = None
			except Exception, e:
				pass
