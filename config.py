DEBUG = True
SQLALCHEMY_TRACK_MODIFICATIONS = False

DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = 'root'
PASSWORD = '256980mm'
HOST = '127.0.0.1'
PORT = '3306'
DATABASE = 'scnuinfo'

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT, DATABASE)