// use flaskdb;

db.divisions.updateOne(
    { name: "Wind Tunnel" },  // Filter to find the document
    {
      $set: {
        name: "WT"  // Update the name field
      }
    }
  );

db.documents.updateMany(
  { division: "Wind Tunnel" },  // Filter to find all matching documents
  {
    $set: {
      division: "WT"  // Update the division field
    }
  }
);

db.users.updateMany(
    { division: "Wind Tunnel" }, // Filter users with the division name "Wind Tunnel"
    {
      $set: {
        division: "WT" // Update the division field to "WT"
      }
    }
  );

db.actionLogs.updateMany(
  { division: "Wind Tunnel" }, // Filter action logs with the division name "Wind Tunnel"
  {
    $set: {
      division: "WT" // Update the division field to "WT"
    }
  }
);

db.users.updateMany(
  { "created_at": { $exists: false } },
  { $set: { "created_at": new Date() } }
)

db.createCollection("slideshowImages");


