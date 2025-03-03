use flaskdb;

// Step 1: Aggregate and store in a temporary collection using $out
db.documents.aggregate([
  {
    $lookup: {
      from: "reportType",
      let: {
        reportTypeName: "$reportType",
        divisionID: "$divisionID"
      },
      pipeline: [
        {
          $match: {
            $expr: {
              $and: [
                { $eq: ["$name", "$$reportTypeName"] },
                { $eq: ["$divisionID", "$$divisionID"] }
              ]
            }
          }
        }
      ],
      as: "reportTypeDetails"
    }
  },
  {
    $unwind: {
      path: "$reportTypeDetails",
      preserveNullAndEmptyArrays: false
    }
  },
  {
    $addFields: {  // Replacing $set with $addFields
      reportTypeID: "$reportTypeDetails._id"
    }
  },
  {
    $project: {  // Replacing $unset with $project
      reportTypeDetails: 0
    }
  },
  {
    $lookup: {
      from: "reportType",
      let: { subReportTypeName: "$subReportType" },
      pipeline: [
        {
          $match: {
            $expr: {
              $and: [
                { $eq: ["$name", "$$subReportTypeName"] },
                { $eq: ["$isSubReportType", true] }
              ]
            }
          }
        }
      ],
      as: "subReportTypeDetails"
    }
  },
  {
    $addFields: {  // Replacing $set with $addFields
      subReportTypeID: {
        $cond: {
          if: { $eq: ["$subReportType", ""] },
          then: null,
          else: { $arrayElemAt: ["$subReportTypeDetails._id", 0] }
        }
      }
    }
  },
  {
    $project: {  // Replacing $unset with $project
      subReportTypeDetails: 0
    }
  },
  {
    $out: "documents_temp" // Using $out instead of $merge for compatibility with older MongoDB versions
  }
]);
