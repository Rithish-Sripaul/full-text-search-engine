// use flaskdb;

db.users.updateMany(
  { isMaster: { $exists: false } },
  { $set: { isMaster: false } }
)

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