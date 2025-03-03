db.documents.deleteMany({});
db.documents.insertMany(db.documents_temp.find().toArray());
db.documents_temp.drop();
