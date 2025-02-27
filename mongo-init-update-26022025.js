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

db.reportType.updateMany(
  { "isCommonToAllDivisions": { $exists: false } },
  { $set: { "isCommonToAllDivisions": false } }
);

db.documents.aggregate([
  {
    $lookup: {
      from: "reportType",
      localField: "reportTypeID",
      foreignField: "_id",
      as: "reportTypeDetails"
    }
  },
  {
    $unwind: {
      path: "$reportTypeDetails",
      preserveNullAndEmptyArrays: true
    }
  },
  {
    $group: {
      _id: {
        divisionID: "$divisionID",
        isCommonToAllDivisions: "$reportTypeDetails.isCommonToAllDivisions"
      },
      count: { $sum: 1 }
    }
  },
  {
    $group: {
      _id: "$_id.divisionID",
      documentCount: {
        $sum: {
          $cond: [
            { $eq: ["$_id.isCommonToAllDivisions", true] },
            0,
            "$count"
          ]
        }
      },
      common_document_count: {
        $sum: {
          $cond: [
            { $eq: ["$_id.isCommonToAllDivisions", true] },
            "$count",
            0
          ]
        }
      }
    }
  },
  {
    $addFields: {
      divisionObjId: { $toObjectId: "$_id" }
    }
  },
  {
    $project: {
      _id: 0,
      divisionObjId: 1,
      documentCount: 1,
      common_document_count: 1
    }
  }
]).forEach(count => {
  db.divisions.updateOne(
    { _id: count.divisionObjId },
    {
      $set: {
        documentCount: count.documentCount,
        common_document_count: count.common_document_count
      }
    }
  );
});

db.divisions.updateMany(
  { "common_document_count": { $exists: false } },
  { $set: { "common_document_count": 0 } }
);
