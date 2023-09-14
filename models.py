from sqlalchemy import create_engine, Column, String, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MasterFileRecord(Base):
    __tablename__ = 'master_file_record'

    uuid = Column(String, primary_key=True)
    file_path = Column(String)
    file_type = Column(String)

class DeletedIds(Base):
    __tablename__ = 'deleted_ids'

    table_type = Column(String)
    faiss_index = Column(Integer)

class Image(Base) :
    __tablename__ = 'image_table'

    faiss_id = Column(String, primary_key=True)
    file_id = Column(String)

class Text(Base) :
    __tablename__ = 'text_table'

    faiss_id = Column(String, primary_key=True)
    file_id = Column(String)
    text_data = Column(String)




# class Store:
#     def __init__(self):
#         self.__is_connected = False

#     def connect(self, store_uri: str):
#         sql_uri = store_uri.split('.')[0] + ".db"
#         self.engine = create_engine(f'sqlite:///{sql_uri}', echo=False)
#         Session = sessionmaker(bind=self.engine)
#         self.session = Session()

#         # Create tables
#         Base.metadata.create_all(self.engine)

#         # Rest of your code remains mostly the same

#     def commit(self):
#         self.session.commit()

#     def _db(self):
#         return self.session
