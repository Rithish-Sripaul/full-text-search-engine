use flaskdb;
db.createUser({
  user: "admin",
  pwd: "1234",
  roles: [
    {
      role: "readWrite",
      db: "flaskdb",
    },
  ],
});

db.createCollection("users");
db.createCollection("documents");
db.createCollection("divisions");
db.createCollection("reportType");
db.createCollection("searchHistory");
db.createCollection("actionLogs");
db.createCollection("slideshowImages");


db.documents.createIndex({ title: "text", content: "text" });

db.divisions.insertMany([
  {
    name: "Wind Tunnel",
    director: "",
    documentCount: 0,
    userCount: 0,
  },
  {
    name: "HSTT",
    director: "",
    documentCount: 0,
    userCount: 0,
  },
  {
    name: "SMB",
    director: "",
    documentCount: 0,
    userCount: 0,
  },
  {
    name: "CT",
    director: "",
    documentCount: 0,
    userCount: 0,
  },
  {
    name: "CFD",
    director: "",
    documentCount: 0,
    userCount: 0,
  },
  {
    name: "LCT",
    director: "",
    documentCount: 0,
    userCount: 0,
  },
]);

