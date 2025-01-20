db = db.getSiblingDB("flaskdb");
db.flaskdb.drop();

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

db.users.insertOne({
  username: "Rithish",
  email: "rithishsripaul@gmail.com",
  password:
    "scrypt:32768:8:1$J11TZPHwMbA9QG1Y$422af6aada97c4da00f68dc54a037a9b44686515091dbd0ce0180a545b77a96767214cce485e5633cc1602780b208fff92f0f1eeccf264a6706474a39aa5fa2d",
  isAdmin: true,
  hasAdminAccount: false,
  adminAccount: null,
});

db.divisions.insertMany([
  {
    name: "Wind Tunnel",
    director: "",
  },
  {
    name: "HSTT",
    director: "",
  },
  {
    name: "SMB",
    director: "",
  },
  {
    name: "CT",
    director: "",
  },
  {
    name: "CFD",
    director: "",
  },
]);

db.divisions.update(
  {},
  { $set: { document_count: 0 } },
  { upsert: false, multi: true }
);

db.reportType.insertMany([
  {
    name: "Research",
    uploaded_by: {
      $oid: "670e33e12ed6c987faad2182",
    },
  },
  {
    name: "Analysis",
    uploaded_by: {
      $oid: "670e33e12ed6c987faad2182",
    },
  },
  {
    name: "Technical",
    uploaded_by: {
      $oid: "670e33e12ed6c987faad2182",
    },
  },
]);

const reportTypes = db.reportType.find({}, { name: 1, _id: 0 }).toArray();
db.divisions.updateMany(
  {},
  {
    $set: {
      reportTypes: reportTypes.map((type) => ({
        name: type.name,
        document_count: 0,
      })),
    },
  }
);

db.documents.insertOne({
  uploadedBy: null,
  title: "Liver Tumor Detection 2",
  year: "2020",
  division: "HSTT",
  author: "Aswin",
  reportType: "Research",
  email: "rithishsripaul@gmail.com",
  file_id: {
    $oid: "67481733e5337e6e7f97c90d",
  },
  isApproved: 0,
  approvedBy: null,
  approved_at: null,
  content:
    "['TANMAYEE SRI J\\nS V RAAMESH\\nT ASWIN KUMAR\\nRITHISH S\\nLIVER TUMORDETECTION\\n21/11/2024\\nCAPSTONE PROJECT', 'AGENDA\\nProblem Statement\\nWhy Is It Important?\\nObjectives\\nOverview\\nSegmentation Problem\\nDataset\\nMethodology\\nResults\\nChallenges \\nLimitations\\nConclusion', 'INTRODUCTION', 'PROBLEM STATEMENT\\nLiver tumor segmentation represents a critical challenge in\\nmedical image analysis, where the complexity of accurately\\ndelineating tumor boundaries from CT scans significantly\\nimpacts diagnostic precision and treatment planning. Current\\nmanual segmentation methods are inherently time-\\nconsuming, subjective, and prone to inter-observer variability,\\nlimiting their effectiveness in clinical settings. \\nThe intricate nature of liver tumors, causes the following\\ncomplication:\\nDiverse shapes, sizes, and subtle boundaries\\nLow contrast between tumorous and healthy tissue\\nThis presents substantial obstacles for reliable automated\\nsegmentation. This research aims to address these\\nchallenges by developing an advanced deep learning\\napproach ', 'Introduction\\nLiver tumor segmentation represents a pivotal advancement in medical imaging\\nwith profound clinical, technological, and patient-centric implications. By enabling\\nprecise, automated delineation of tumor boundaries, this approach addresses\\ncritical healthcare challenges, including early detection, accurate treatment\\nplanning, and personalized medical interventions. Traditional manual segmentation\\nmethods are inherently limited by time-consuming processes, subjective\\ninterpretation, and significant inter-observer variability, which can compromise\\ndiagnostic accuracy and patient outcomes. Advanced deep learning techniques\\noffer a transformative solution, potentially reducing diagnostic time by 60-70%,\\nminimizing human error, and providing standardized, reproducible tumor volume\\nmeasurements. The technological significance extends beyond individual patient\\ncare, promising substantial economic benefits by optimizing healthcare resource\\nallocation, reducing unnecessary invasive procedures, and supporting more\\nefficient treatment strategies. Moreover, automated segmentation techniques\\ndemocratize high-quality medical imaging analysis, making sophisticated\\ndiagnostic capabilities more accessible across varying healthcare settings,\\nultimately improving survival rates, enabling real-time treatment monitoring, and\\nsupporting data-driven, personalized medical decision-making in liver tumor\\nmanagement. 3\\nWHY IS IT IMPORTANT?', 'CURRENT PRACTICES AND LIMITATIONS\\nLiver Tumor Detection\\nmethods in use\\nManual examination of CT/MRI\\nscans by radiologists.\\n-and-\\nSemi-automated tools with\\nlimited AI integration.\\nShortcomings of Traditional\\nmodels\\nManual Diagnosis\\nTime-intensive process reliant on\\nradiologist expertise.\\nExisting Tools\\nLow accuracy and high error\\nrates in real-world clinical\\napplications.\\nPoor generalization across\\ndiverse patient datasets.', 'PROJECT OBJECTIVES\\nEarly and Accurate Tumor Detection\\nDevelop a reliable system to identify\\nliver tumors at an early stage with high\\nprecision.\\nAdvancing Medical Technology\\nUtilize cutting-edge deep learning\\nmodels to enhance diagnostic tools and\\nsupport radiologists\\nScope of the project\\nFocus on automating liver tumor\\ndetection using CT scan imaging.\\nCompare multiple state-of-the-art\\narchitectures (EfficientNet,\\nDenseNet, ResNet) to identify the\\nmost effective model.\\nProvide a scalable and generalizable\\nsolution applicable to diverse\\ndatasets', '4\\nLiver tumor segmentation is a critical challenge in medical\\nimaging analysis, with significant implications for early\\ndiagnosis, treatment planning, and patient outcomes.\\nThe complex morphology of liver tumors, characterized by\\ndiverse shapes, sizes, and subtle boundaries, presents\\nsubstantial obstacles for reliable automated segmentation.\\nCurrent manual segmentation methods are time-consuming,\\nsubjective, and prone to inter-observer variability, limiting their\\neffectiveness in clinical settings.\\nAdvanced deep learning architectures, such as EfficientNet B3,\\nB5, DenseNet121, and ResNet50, offer a promising solution to\\naddress the limitations of existing segmentation approaches.\\nBy developing a robust, automated liver tumor segmentation\\nmethodology, this research aims to enhance diagnostic accuracy,\\nreduce variability, and ultimately improve medical image analysis\\ncapabilities for better patient care.\\nOVERVIEW', 'LiTS (Liver Tumor Segmentation Challenge)\\ndataset. This dataset is part of the Liver Tumor\\nSegmentation Challenge (LiTS17) from 2017,\\ndesigned to advance automatic segmentation\\nalgorithms for liver tumors in contrast-enhanced\\nCT scans. \\nThe dataset was sourced from multiple clinical\\nsites worldwide and made publicly available for\\nthe LiTS Challenge 2017, organized in\\nconjunction with ISBI 2017 and MICCAI 2017.\\nThe dataset contains 130 CT scans, each\\ncontaining liver and tumor lesion images.\\nManual Annotations: The dataset provides\\nground truth segmentation masks, manually\\nannotated by medical experts, highlighting the\\nliver and tumor lesions.\\nImage Types:\\nCT Scan Images: Each scan contains a series of\\nslices that represent cross-sectional views of\\nthe liver and surrounding organs.\\nDATASET OVERVIEW', 'METHODOLOGY\\nFully Convolutional Network (FCN)\\ndesigned for precise image\\nsegmentation\\nEncoder-decoder structure with skip\\nconnections to preserve fine-grained\\ndetails and spatial information\\nUsed for accurate delineation of liver\\ntumors in CT scans\\nModel Architecture: U-Net EfficientNetB5 Backbone:\\nEfficientNetB5 is a pre-trained model\\nknown for its efficiency and high\\nperformance with fewer parameters for\\nfeature extraction\\nOptimized to provide robust feature\\nextraction from CT images, particularly\\nimportant for detecting small or irregular\\nliver tumors\\nFaster inference and reduced overfitting\\ncompared to other backbone options', 'Model Framework Loss Function and Metrics\\nLoss Function: CrossEntropyLoss for\\nmulticlass segmentation.\\nMetrics:\\nForeground Accuracy: Evaluates\\naccuracy excluding the\\nbackground.\\nCustom Foreground Accuracy:\\nIncludes background in\\naccuracy calculation.\\nEfficientNet-B5 acts as the encoder\\nin a U-Net architecture.\\nPre-trained weights leveraged for\\ntransfer learning.\\nCombines high accuracy with computational efficiency.\\nScaled-up version of EfficientNet optimized for better performance in image\\nanalysis tasks.\\nWHY EFFECIENTNET-B5?', 'DATASETSOURCE\\nMedical CT scandatasets with labeledliver tumor regions.\\nDATA\\nCHARACTERISTICS\\nHigh-resolution scanswith tumor/non-tumorclassifications.\\nImplementation Steps\\nDataCollection', 'T R A I N I N G  P R O C E S S\\nUsed the Adam optimizer\\nwith a learning rate\\nscheduler to ensure\\nsmooth training and\\nconvergence.\\nWeight decay (wd=0.1)\\nwas applied for\\nregularization.\\nAugmented data with random\\nrotations, flips, and zoom to\\nimprove model generalization\\nand reduce overfitting.\\nData Augmentation:\\nCrossEntropyLossFlat with\\naxis=1, used to calculate\\nloss for multi-class\\nsegmentation, focusing on\\nforeground-background\\ndifferentiation.\\nLoss Function: Optimization:\\nFine-tuned the model over 10 epochs for better accuracy.', 'T R A I N I N G  P R O C E S S\\nFine-tuned the pre-trained\\nEfficientNetB5 model for\\n10 epochs to adapt it to\\nliver tumor segmentation\\ntasks.\\nFine-tuning:\\nSaveModelCallback: Saves the\\nmodel when the validation loss\\nimproves.\\nEarlyStoppingCallback: Stops\\ntraining early if validation loss\\ndoes not improve for 3\\nconsecutive epochs.\\nCallbacks:', 'IMAGES AND VISUALS', 'IMAGES AND VISUALS', 'COMPARISSION OF MODELS\\n', 'COMPARISSION OF MODELS', 'KEYFINDINGS AND RESULTS\\nModel Performance\\nAchieved 99.89% Accuracy using\\nthe EfficientNet-B5 model.\\nHigh precision and reliability in\\ndetecting liver tumors.\\n Performance Metrics\\nForeground Accuracy: Achieved 97%,\\ndemonstrating reliable prediction in\\nnon-background regions.\\nComparison with Existing Methods\\nSignificant improvement over\\ntraditional models and earlier\\napproaches.\\nHighlights the potential of\\ndeep learning in advancing\\nmedical diagnostics.\\n', 'Expand training with diverse\\ndatasets to improve generalization\\nacross different imaging protocols\\nand patient demographics.\\nExplore other medical imaging tasks\\n(e.g., lung, brain tumors).\\nModel Generalization\\nFUTURE SCOPE\\nImplement techniques like Grad-CAM\\nand SHAP to improve model\\ntransparency and clinician trust.\\nInterpretability', 'Advanced model:\\nDeveloped a liver tumor segmentation model using U-Net with various backbones (ResNet, DenseNet,\\nEfficientNetB5) to enhance feature extraction and segmentation accuracy.\\nOptimized Performance:\\nLeveraged the strengths of each backbone (e.g., EfficientNetB5 for efficiency, ResNet for deeper feature\\nlearning, DenseNet for better feature reuse) to improve accuracy and efficiency in tumor delineation.\\nClinical Impact:\\nThe model reduces manual intervention, providing faster, more accurate, and reproducible tumor\\nsegmentation for liver cancer diagnosis and treatment planning.\\nFuture Expansion:\\nPotential for further advancements, including multimodal integration, real-time deployment, and\\npersonalized treatment strategies.\\nO U R  C O N C L U S I O N', 'R I T H I S H  S                   2 1 B C E 8 8 2 9\\nT A N M A Y E E  S R I  J         2 1 B C E 7 6 4 7\\nT  A S W I N  K U M A R         2 1 B C E 8 8 5 9\\nS . V . R A A M E S H             2 1 B C E 8 8 4 1\\nThank you!']",
  uploaded_at: {
    $date: "2024-11-28T12:39:39.631Z",
  },
});

print("Database initialized with test data.");
