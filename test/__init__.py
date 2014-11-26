import unittest
import sys
sys.path.append('/Users/igor/Develop/local/PySQLPool/test/')

def suite():
	modules = ['testConnection', 'testPool', 'testQuery', 'testTransaction', 'testLogging']
	alltests = unittest.TestSuite()
	for module in map(__import__, modules):
		alltests.addTest(unittest.findTestCases(module))
		
	return alltests

if __name__ == "__main__":
	unittest.main(defaultTest="suite")