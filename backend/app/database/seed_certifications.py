"""
Certification Intelligence Engine seed data.
40 certifications (10 per branch: AIML, ECE, EEE, Mechanical).
Covers major providers: NPTEL, Microsoft, Google, AWS, Cisco, Infosys, Intel, Texas Instruments, NVIDIA.
Includes prerequisites, skills, benefits, and exam details.
"""

CERTIFICATION_SEED = {
    "AIML": [
        {
            "title": "NPTEL: Deep Learning for Computer Vision",
            "provider": "NPTEL (IIT Kharagpur)", "provider_type": "NPTEL",
            "description": "12-week NPTEL course covering deep learning architectures, CNNs, object detection, and generative models.",
            "official_url": "https://nptel.ac.in/courses/106/105/106105215/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 40, "semester_num": 4,
            "skills": [("TensorFlow", "INTERMEDIATE"), ("Computer Vision", "INTERMEDIATE"), ("Machine Learning", "BEGINNER")],
            "prereqs": [
                {"course_title": "Deep Learning with TensorFlow", "min_score": 60.0},
            ],
            "exams": [
                {"name": "NPTEL Proctored Certification Exam", "duration": "180 mins", "score": 75.0, "pattern": "Proctored MCQ + Numerical problem solving", "link": "https://nptel.ac.in/noc/"},
            ],
            "benefits": [
                {"benefit": "Academic credit transfer eligibility (3 credits)", "order": 1},
                {"benefit": "Direct alignment with computer vision engineering roles", "order": 2},
                {"benefit": "Top 5% score gold certificate highlighted by faculty", "order": 3},
            ],
        },
        {
            "title": "AWS Certified Machine Learning – Specialty",
            "provider": "Amazon Web Services", "provider_type": "AWS",
            "description": "Validates expertise in building, training, tuning, and deploying ML models on AWS SageMaker.",
            "official_url": "https://aws.amazon.com/certification/certified-machine-learning-specialty/",
            "difficulty": "ADVANCED", "estimated_hours": 60, "semester_num": 6,
            "skills": [("Machine Learning", "ADVANCED"), ("Python", "ADVANCED"), ("TensorFlow", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "MLOps & Model Deployment", "min_score": 70.0},
            ],
            "exams": [
                {"name": "AWS MLS-C01 Exam", "duration": "180 mins", "score": 750.0, "pattern": "65 multiple choice and multiple response questions", "link": "https://aws.amazon.com/certification/"},
            ],
            "benefits": [
                {"benefit": "Global industry recognition for cloud ML engineering roles", "order": 1},
                {"benefit": "High placement advantage for enterprise cloud AI teams", "order": 2},
                {"benefit": "Access to AWS Certified Global Network", "order": 3},
            ],
        },
        {
            "title": "TensorFlow Developer Certificate",
            "provider": "Google", "provider_type": "Google",
            "description": "Demonstrates proficiency in using TensorFlow to solve computer vision, NLP, and time-series problems.",
            "official_url": "https://www.tensorflow.org/certificate",
            "difficulty": "INTERMEDIATE", "estimated_hours": 45, "semester_num": 5,
            "skills": [("TensorFlow", "ADVANCED"), ("Python", "ADVANCED"), ("Computer Vision", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Deep Learning with TensorFlow", "min_score": 65.0},
            ],
            "exams": [
                {"name": "Google TensorFlow Developer Exam", "duration": "300 mins", "score": 80.0, "pattern": "Hands-on model building exam using PyCharm IDE plugin", "link": "https://www.tensorflow.org/certificate"},
            ],
            "benefits": [
                {"benefit": "Listed on Google's official TensorFlow Certified Developers directory", "order": 1},
                {"benefit": "Resume boost for AI/ML specialist shortlisting", "order": 2},
            ],
        },
        {
            "title": "NVIDIA Certified Associate: Generative AI & LLMs",
            "provider": "NVIDIA", "provider_type": "NVIDIA",
            "description": "Validates foundational knowledge of Generative AI architectures, Transformers, and GPU acceleration.",
            "official_url": "https://www.nvidia.com/en-us/training/certification/",
            "difficulty": "ADVANCED", "estimated_hours": 50, "semester_num": 7,
            "skills": [("Machine Learning", "ADVANCED"), ("Python", "ADVANCED"), ("TensorFlow", "ADVANCED")],
            "prereqs": [
                {"course_title": "Natural Language Processing", "min_score": 75.0},
            ],
            "exams": [
                {"name": "NVIDIA Generative AI Associate Exam", "duration": "90 mins", "score": 70.0, "pattern": "Online proctored MCQs on transformer architecture and GPU optimization", "link": "https://www.nvidia.com/en-us/training/"},
            ],
            "benefits": [
                {"benefit": "Industry endorsement from leading AI hardware manufacturer", "order": 1},
                {"benefit": "Unlocks preferred candidacy for NVIDIA partner ecosystem roles", "order": 2},
            ],
        },
        {
            "title": "Microsoft Certified: Azure AI Engineer Associate",
            "provider": "Microsoft", "provider_type": "Microsoft",
            "description": "Validates expertise in building Cognitive Services, Azure OpenAI, and bot solutions on Azure.",
            "official_url": "https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-engineer/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 40, "semester_num": 5,
            "skills": [("Machine Learning", "INTERMEDIATE"), ("Python", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Machine Learning Fundamentals", "min_score": 60.0},
            ],
            "exams": [
                {"name": "Microsoft Exam AI-102", "duration": "120 mins", "score": 700.0, "pattern": "Multiple choice, case studies, and performance-based labs", "link": "https://learn.microsoft.com/"},
            ],
            "benefits": [
                {"benefit": "Official Microsoft credential for enterprise AI development", "order": 1},
                {"benefit": "Increases campus placement interview calls by 3x", "order": 2},
            ],
        },
        {
            "title": "Infosys Springboard: Artificial Intelligence Specialist",
            "provider": "Infosys", "provider_type": "Infosys",
            "description": "Comprehensive corporate training path covering Python, scikit-learn, and deep learning for enterprise applications.",
            "official_url": "https://infyspringboard.onwingspan.com/",
            "difficulty": "BEGINNER", "estimated_hours": 30, "semester_num": 3,
            "skills": [("Python", "INTERMEDIATE"), ("Machine Learning", "BEGINNER")],
            "prereqs": [
                {"course_title": "Python for AI & Data Science", "min_score": 50.0},
            ],
            "exams": [
                {"name": "Infosys Springboard AI Assessment", "duration": "90 mins", "score": 65.0, "pattern": "MCQ and coding assessment on Infosys platform", "link": "https://infyspringboard.onwingspan.com/"},
            ],
            "benefits": [
                {"benefit": "Direct fast-track interview opportunity for Infosys Specialist Programmer role", "order": 1},
                {"benefit": "Free accessible industry training certification", "order": 2},
            ],
        },
        {
            "title": "Intel Edge AI Developer Certification",
            "provider": "Intel", "provider_type": "Intel",
            "description": "Certifies ability to optimize deep learning models for edge deployment using Intel OpenVINO toolkit.",
            "official_url": "https://www.intel.com/content/www/us/en/developer/tools/openvino-toolkit/certification.html",
            "difficulty": "ADVANCED", "estimated_hours": 35, "semester_num": 6,
            "skills": [("Computer Vision", "ADVANCED"), ("Python", "ADVANCED")],
            "prereqs": [
                {"course_title": "Computer Vision with OpenCV", "min_score": 70.0},
            ],
            "exams": [
                {"name": "Intel OpenVINO Developer Assessment", "duration": "120 mins", "score": 75.0, "pattern": "Hands-on notebook submission optimizing inference pipeline", "link": "https://intel.com/developer"},
            ],
            "benefits": [
                {"benefit": "Specialized edge AI credential valued in robotics and IoT startups", "order": 1},
            ],
        },
        {
            "title": "Coursera: Deep Learning Specialization by Andrew Ng",
            "provider": "Coursera / DeepLearning.AI", "provider_type": "Coursera",
            "description": "5-course series covering Neural Networks, Hyperparameter Tuning, Structuring ML Projects, CNNs, and Sequence Models.",
            "official_url": "https://www.coursera.org/specializations/deep-learning",
            "difficulty": "INTERMEDIATE", "estimated_hours": 60, "semester_num": 4,
            "skills": [("Machine Learning", "ADVANCED"), ("TensorFlow", "INTERMEDIATE"), ("Python", "ADVANCED")],
            "prereqs": [
                {"course_title": "Machine Learning Fundamentals", "min_score": 65.0},
            ],
            "exams": [
                {"name": "5 Specialization Course Assessments", "duration": "Self-paced", "score": 80.0, "pattern": "Weekly programming assignments in Python and MCQs", "link": "https://coursera.org"},
            ],
            "benefits": [
                {"benefit": "Most globally recognized foundational deep learning certificate", "order": 1},
                {"benefit": "Essential resume benchmark for AI master's and research roles", "order": 2},
            ],
        },
        {
            "title": "Google Cloud Professional Data Engineer",
            "provider": "Google Cloud", "provider_type": "Google",
            "description": "Validates ability to design data processing systems, build operational ML pipelines, and manage BigQuery.",
            "official_url": "https://cloud.google.com/certification/data-engineer",
            "difficulty": "ADVANCED", "estimated_hours": 50, "semester_num": 7,
            "skills": [("Machine Learning", "ADVANCED"), ("Python", "ADVANCED")],
            "prereqs": [
                {"course_title": "MLOps & Model Deployment", "min_score": 75.0},
            ],
            "exams": [
                {"name": "GCP Data Engineer Exam", "duration": "120 mins", "score": 70.0, "pattern": "50 multiple choice and multiple select questions", "link": "https://cloud.google.com/certification/"},
            ],
            "benefits": [
                {"benefit": "Top tier salary credential in data engineering and MLOps", "order": 1},
            ],
        },
        {
            "title": "Oracle Cloud Infrastructure 2024 AI Certified Associate",
            "provider": "Oracle", "provider_type": "Oracle",
            "description": "Certifies foundational OCI AI services including OCI Vision, Speech, Language, and Generative AI service integration.",
            "official_url": "https://education.oracle.com/oci-ai-certified-associate",
            "difficulty": "BEGINNER", "estimated_hours": 25, "semester_num": 3,
            "skills": [("Python", "INTERMEDIATE"), ("Machine Learning", "BEGINNER")],
            "prereqs": [
                {"course_title": "Python for AI & Data Science", "min_score": 50.0},
            ],
            "exams": [
                {"name": "Oracle 1Z0-1122-24 Exam", "duration": "90 mins", "score": 68.0, "pattern": "55 multiple-choice questions online", "link": "https://education.oracle.com/"},
            ],
            "benefits": [
                {"benefit": "Vendor certificate for enterprise cloud AI implementation", "order": 1},
            ],
        },
    ],
    "ECE": [
        {
            "title": "Texas Instruments Robotics & Embedded Systems Certification",
            "provider": "Texas Instruments", "provider_type": "Texas Instruments",
            "description": "Hands-on certification covering LaunchPad MSP430/MSP432 microcontrollers, sensor interfacing, and motor control.",
            "official_url": "https://www.ti.com/university",
            "difficulty": "INTERMEDIATE", "estimated_hours": 35, "semester_num": 3,
            "skills": [("C Programming", "INTERMEDIATE"), ("Embedded C", "INTERMEDIATE"), ("Arduino", "BEGINNER")],
            "prereqs": [
                {"course_title": "C Programming for Engineers", "min_score": 60.0},
            ],
            "exams": [
                {"name": "TI University Embedded Exam", "duration": "90 mins", "score": 70.0, "pattern": "Lab practical + theoretical MCQs", "link": "https://ti.com/university"},
            ],
            "benefits": [
                {"benefit": "Direct recognition by TI partner companies hiring embedded hardware engineers", "order": 1},
                {"benefit": "Covers core microcontrollers used in industrial product design", "order": 2},
            ],
        },
        {
            "title": "Cisco Certified Network Associate (CCNA 200-301)",
            "provider": "Cisco Systems", "provider_type": "Cisco",
            "description": "Industry-standard certification covering network fundamentals, IP connectivity, security fundamentals, and automation.",
            "official_url": "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html",
            "difficulty": "INTERMEDIATE", "estimated_hours": 60, "semester_num": 4,
            "skills": [("Signal Processing", "BEGINNER"), ("C Programming", "BEGINNER")],
            "prereqs": [
                {"course_title": "Digital Electronics & Logic Design", "min_score": 50.0},
            ],
            "exams": [
                {"name": "Cisco 200-301 CCNA Exam", "duration": "120 mins", "score": 825.0, "pattern": "Multiple choice, drag-and-drop, and Packet Tracer simulation labs", "link": "https://cisco.com"},
            ],
            "benefits": [
                {"benefit": "Gold standard certification for telecommunications and networking engineers", "order": 1},
                {"benefit": "Required by core telecom employers like BSNL, Airtel, Cisco, and Nokia", "order": 2},
            ],
        },
        {
            "title": "NPTEL: Microprocessors and Microcontrollers",
            "provider": "NPTEL (IIT Kharagpur)", "provider_type": "NPTEL",
            "description": "12-week course on 8085, 8086, 8051 and ARM architectures with assembly and C programming.",
            "official_url": "https://nptel.ac.in/courses/108/105/108105102/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 40, "semester_num": 4,
            "skills": [("Embedded C", "INTERMEDIATE"), ("Digital Electronics", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "C Programming for Engineers", "min_score": 60.0},
            ],
            "exams": [
                {"name": "NPTEL Proctored Exam", "duration": "180 mins", "score": 60.0, "pattern": "Proctored MCQs and assembly language problems", "link": "https://nptel.ac.in"},
            ],
            "benefits": [
                {"benefit": "Fulfills 3 academic elective credit requirements at GITAM", "order": 1},
                {"benefit": "Solid foundation for GATE ECE examination", "order": 2},
            ],
        },
        {
            "title": "Arm Accredited Engineer (AAE)",
            "provider": "Arm", "provider_type": "Others",
            "description": "Validates comprehensive knowledge of Arm Cortex-M architecture, assembly language, and low-level debugging.",
            "official_url": "https://www.arm.com/resources/education/accreditation",
            "difficulty": "ADVANCED", "estimated_hours": 50, "semester_num": 5,
            "skills": [("STM32", "ADVANCED"), ("Embedded C", "ADVANCED"), ("C Programming", "ADVANCED")],
            "prereqs": [
                {"course_title": "STM32 Microcontroller Programming", "min_score": 70.0},
            ],
            "exams": [
                {"name": "Arm Accredited Engineer Exam", "duration": "90 mins", "score": 70.0, "pattern": "Proctored online exam covering Cortex-M architecture details", "link": "https://arm.com"},
            ],
            "benefits": [
                {"benefit": "Top global credential for Cortex-M firmware engineers", "order": 1},
                {"benefit": "Significant edge in semiconductor and automotive design company placements", "order": 2},
            ],
        },
        {
            "title": "Intel Edge AI for IoT Developers",
            "provider": "Intel", "provider_type": "Intel",
            "description": "Certifies capability to deploy computer vision and deep learning inference on Intel Movidius VPU and edge hardware.",
            "official_url": "https://www.intel.com/content/www/us/en/developer/topic-technology/edge-5g/overview.html",
            "difficulty": "ADVANCED", "estimated_hours": 35, "semester_num": 6,
            "skills": [("STM32", "INTERMEDIATE"), ("Embedded C", "INTERMEDIATE"), ("Signal Processing", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Internet of Things (IoT) Systems", "min_score": 65.0},
            ],
            "exams": [
                {"name": "Intel IoT Assessment", "duration": "90 mins", "score": 75.0, "pattern": "Coding lab and MCQ exam", "link": "https://intel.com"},
            ],
            "benefits": [
                {"benefit": "Specialized credential for IoT and smart hardware design roles", "order": 1},
            ],
        },
        {
            "title": "Coursera: An Introduction to Programming the Internet of Things (IoT)",
            "provider": "Coursera / UC Irvine", "provider_type": "Coursera",
            "description": "6-course specialization covering Arduino, Raspberry Pi, C, Python, and cloud sensor integration.",
            "official_url": "https://www.coursera.org/specializations/iot",
            "difficulty": "BEGINNER", "estimated_hours": 40, "semester_num": 3,
            "skills": [("Arduino", "INTERMEDIATE"), ("C Programming", "BEGINNER")],
            "prereqs": [
                {"course_title": "Embedded Systems with Arduino", "min_score": 50.0},
            ],
            "exams": [
                {"name": "Specialization Capstone Assessment", "duration": "Self-paced", "score": 80.0, "pattern": "Hands-on project peer review + quizzes", "link": "https://coursera.org"},
            ],
            "benefits": [
                {"benefit": "Broad foundational IoT certificate valued by embedded startups", "order": 1},
            ],
        },
        {
            "title": "NVIDIA Deep Learning Institute: Fundamentals of Deep Learning",
            "provider": "NVIDIA", "provider_type": "NVIDIA",
            "description": "Hands-on training on training neural networks on GPUs for computer vision and signal applications.",
            "official_url": "https://www.nvidia.com/en-us/training/online/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 20, "semester_num": 5,
            "skills": [("Signal Processing", "INTERMEDIATE"), ("C Programming", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Signal Processing & MATLAB", "min_score": 60.0},
            ],
            "exams": [
                {"name": "NVIDIA DLI Certificate Assessment", "duration": "480 mins", "score": 80.0, "pattern": "Hands-on cloud Jupyter notebook task solving", "link": "https://nvidia.com/dli"},
            ],
            "benefits": [
                {"benefit": "NVIDIA DLI certificate recognized by AI hardware and signal processing labs", "order": 1},
            ],
        },
        {
            "title": "Cadence Certified Virtuoso Layout Design Associate",
            "provider": "Cadence", "provider_type": "Others",
            "description": "Validates proficiency in IC layout design, DRC, and LVS checks using Cadence Virtuoso suite.",
            "official_url": "https://www.cadence.com/en_US/home/training/all-courses.html",
            "difficulty": "ADVANCED", "estimated_hours": 50, "semester_num": 6,
            "skills": [("Digital Electronics", "ADVANCED"), ("PCB Design", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "VLSI Design Fundamentals", "min_score": 70.0},
            ],
            "exams": [
                {"name": "Cadence Virtuoso Exam", "duration": "120 mins", "score": 70.0, "pattern": "Layout design lab test and theory MCQs", "link": "https://cadence.com"},
            ],
            "benefits": [
                {"benefit": "Essential qualification for VLSI physical design engineer placements", "order": 1},
                {"benefit": "Key differentiator for Qualcomm, Intel, Synopsys campus recruitment", "order": 2},
            ],
        },
        {
            "title": "AWS Certified SysOps Administrator – Associate",
            "provider": "AWS", "provider_type": "AWS",
            "description": "Validates technical expertise in deployment, management, and operations on AWS for IoT and edge infrastructure.",
            "official_url": "https://aws.amazon.com/certification/certified-sysops-admin-associate/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 45, "semester_num": 5,
            "skills": [("Arduino", "INTERMEDIATE"), ("C Programming", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Embedded Systems with Arduino", "min_score": 60.0},
            ],
            "exams": [
                {"name": "AWS SOA-C02 Exam", "duration": "130 mins", "score": 720.0, "pattern": "MCQs, multiple response, and exam labs", "link": "https://aws.amazon.com"},
            ],
            "benefits": [
                {"benefit": "Strong resume credential for cloud hardware and edge systems engineering", "order": 1},
            ],
        },
        {
            "title": "Infosys Springboard: Embedded Systems & Microcontrollers",
            "provider": "Infosys", "provider_type": "Infosys",
            "description": "Corporate training path covering 8051, ARM, Embedded C, and real-time operating systems.",
            "official_url": "https://infyspringboard.onwingspan.com/",
            "difficulty": "BEGINNER", "estimated_hours": 30, "semester_num": 3,
            "skills": [("C Programming", "INTERMEDIATE"), ("Embedded C", "BEGINNER")],
            "prereqs": [
                {"course_title": "C Programming for Engineers", "min_score": 50.0},
            ],
            "exams": [
                {"name": "Infosys Embedded Assessment", "duration": "90 mins", "score": 65.0, "pattern": "MCQs and practical C programming evaluation", "link": "https://infyspringboard.onwingspan.com/"},
            ],
            "benefits": [
                {"benefit": "Fast-track shortlisting for Infosys Systems Engineer (Embedded) drive", "order": 1},
            ],
        },
    ],
    "EEE": [
        {
            "title": "NPTEL: Power Electronics",
            "provider": "NPTEL (IIT Delhi)", "provider_type": "NPTEL",
            "description": "12-week comprehensive NPTEL course covering power semiconductor devices, converters, inverters, and PWM control.",
            "official_url": "https://nptel.ac.in/courses/108/102/108102145/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 40, "semester_num": 3,
            "skills": [("Power Systems", "INTERMEDIATE"), ("MATLAB", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Power Electronics & Converters", "min_score": 60.0},
            ],
            "exams": [
                {"name": "NPTEL Proctored Exam", "duration": "180 mins", "score": 60.0, "pattern": "Proctored MCQs and converter design problems", "link": "https://nptel.ac.in"},
            ],
            "benefits": [
                {"benefit": "Academic credit transfer (3 credits) for EEE degree", "order": 1},
                {"benefit": "Foundational preparation for GATE EEE paper", "order": 2},
            ],
        },
        {
            "title": "Siemens Certified PLC Programmer (S7-1200 / S7-1500)",
            "provider": "Others", "provider_type": "Others",
            "description": "Industry certification for programming Siemens S7 PLCs using TIA Portal, ladder logic, function block diagrams, and SCADA.",
            "official_url": "https://www.siemens.com/global/en/products/services/industry/sitrain.html",
            "difficulty": "ADVANCED", "estimated_hours": 50, "semester_num": 5,
            "skills": [("PLC Programming", "ADVANCED"), ("SCADA", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "PLC Programming & Industrial Automation", "min_score": 70.0},
            ],
            "exams": [
                {"name": "Siemens Sitrain Certification Exam", "duration": "120 mins", "score": 70.0, "pattern": "Practical PLC programming task in TIA Portal + MCQs", "link": "https://siemens.com/sitrain"},
            ],
            "benefits": [
                {"benefit": "Highest industry value for industrial automation and power plant jobs", "order": 1},
                {"benefit": "Direct qualification for Siemens, ABB, Schneider Electric hiring drives", "order": 2},
            ],
        },
        {
            "title": "Schneider Electric Energy Management Associate",
            "provider": "Others", "provider_type": "Others",
            "description": "Certifies competence in energy auditing, power quality analysis, smart metering, and ISO 50001 compliance.",
            "official_url": "https://www.se.com/ww/en/about-us/careers/events/energy-university.jsp",
            "difficulty": "INTERMEDIATE", "estimated_hours": 30, "semester_num": 4,
            "skills": [("Power Systems", "INTERMEDIATE"), ("SCADA", "BEGINNER")],
            "prereqs": [
                {"course_title": "Power Electronics & Converters", "min_score": 50.0},
            ],
            "exams": [
                {"name": "Schneider Energy University Exam", "duration": "60 mins", "score": 75.0, "pattern": "Online multiple-choice assessment", "link": "https://se.com"},
            ],
            "benefits": [
                {"benefit": "Recognized credential for energy auditor and sustainability roles", "order": 1},
            ],
        },
        {
            "title": "MathWorks Certified MATLAB Associate",
            "provider": "Others", "provider_type": "Others",
            "description": "Validates core proficiency in MATLAB programming, data processing, visualization, and Simulink model simulation.",
            "official_url": "https://www.mathworks.com/services/training/certification.html",
            "difficulty": "INTERMEDIATE", "estimated_hours": 35, "semester_num": 4,
            "skills": [("MATLAB", "ADVANCED"), ("Power Systems", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Control Systems Engineering", "min_score": 65.0},
            ],
            "exams": [
                {"name": "MathWorks Certified MATLAB Associate Exam", "duration": "90 mins", "score": 70.0, "pattern": "Multiple-choice online exam on MATLAB environment and syntax", "link": "https://mathworks.com/certification"},
            ],
            "benefits": [
                {"benefit": "Global official credential for modeling and simulation engineers", "order": 1},
                {"benefit": "Strong resume booster for R&D placements", "order": 2},
            ],
        },
        {
            "title": "Texas Instruments Power Management Certification",
            "provider": "Texas Instruments", "provider_type": "Texas Instruments",
            "description": "Hands-on training on DC-DC converter topologies, LDO design, PMIC integration, and thermal management.",
            "official_url": "https://dev.ti.com/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 30, "semester_num": 4,
            "skills": [("Power Systems", "INTERMEDIATE"), ("MATLAB", "BEGINNER")],
            "prereqs": [
                {"course_title": "Power Electronics & Converters", "min_score": 60.0},
            ],
            "exams": [
                {"name": "TI Power Management Exam", "duration": "90 mins", "score": 70.0, "pattern": "Online quiz + WEBENCH Power Designer lab task", "link": "https://ti.com"},
            ],
            "benefits": [
                {"benefit": "Recognized by power supply design and EV power electronics firms", "order": 1},
            ],
        },
        {
            "title": "AWS Certified Solutions Architect – Associate",
            "provider": "AWS", "provider_type": "AWS",
            "description": "Validates ability to design resilient, high-performing, decoupled cloud architecture for smart grid IoT data.",
            "official_url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 50, "semester_num": 6,
            "skills": [("SCADA", "INTERMEDIATE"), ("Power Systems", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Smart Grid & Energy Management", "min_score": 65.0},
            ],
            "exams": [
                {"name": "AWS SAA-C03 Exam", "duration": "130 mins", "score": 720.0, "pattern": "65 multiple choice and multiple response questions", "link": "https://aws.amazon.com"},
            ],
            "benefits": [
                {"benefit": "Top global cloud architecture credential", "order": 1},
                {"benefit": "Opens high-paying roles in smart energy cloud platforms", "order": 2},
            ],
        },
        {
            "title": "NPTEL: Power System Analysis",
            "provider": "NPTEL (IIT Kanpur)", "provider_type": "NPTEL",
            "description": "12-week course on bus admittance, load flow, symmetrical components, fault calculations, and power stability.",
            "official_url": "https://nptel.ac.in/courses/108/106/108106074/",
            "difficulty": "ADVANCED", "estimated_hours": 45, "semester_num": 5,
            "skills": [("Power Systems", "ADVANCED"), ("MATLAB", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Power Systems Analysis", "min_score": 65.0},
            ],
            "exams": [
                {"name": "NPTEL Proctored Exam", "duration": "180 mins", "score": 60.0, "pattern": "Proctored MCQs and load flow numerical problems", "link": "https://nptel.ac.in"},
            ],
            "benefits": [
                {"benefit": "Essential credit course for core EEE higher studies and GATE", "order": 1},
            ],
        },
        {
            "title": "Google Professional Cloud Architect",
            "provider": "Google Cloud", "provider_type": "Google",
            "description": "Demonstrates capability to leverage GCP infrastructure to design secure, scalable solutions for industrial IoT.",
            "official_url": "https://cloud.google.com/certification/cloud-architect",
            "difficulty": "ADVANCED", "estimated_hours": 55, "semester_num": 7,
            "skills": [("SCADA", "ADVANCED"), ("Power Systems", "ADVANCED")],
            "prereqs": [
                {"course_title": "Smart Grid & Energy Management", "min_score": 75.0},
            ],
            "exams": [
                {"name": "GCP Cloud Architect Exam", "duration": "120 mins", "score": 70.0, "pattern": "Case study analysis and multiple-choice questions", "link": "https://cloud.google.com"},
            ],
            "benefits": [
                {"benefit": "Highest rated enterprise cloud architect certification", "order": 1},
            ],
        },
        {
            "title": "Cisco Certified DevNet Associate",
            "provider": "Cisco Systems", "provider_type": "Cisco",
            "description": "Validates core software development and design skills including network automation, security, and SCADA APIs.",
            "official_url": "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/devnet/devnet-associate.html",
            "difficulty": "INTERMEDIATE", "estimated_hours": 40, "semester_num": 5,
            "skills": [("PLC Programming", "INTERMEDIATE"), ("SCADA", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "PLC Programming & Industrial Automation", "min_score": 60.0},
            ],
            "exams": [
                {"name": "Cisco 200-901 DEVASC Exam", "duration": "120 mins", "score": 825.0, "pattern": "MCQs, drag-and-drop, and API automation scenarios", "link": "https://cisco.com"},
            ],
            "benefits": [
                {"benefit": "Bridges industrial automation and modern software engineering", "order": 1},
            ],
        },
        {
            "title": "Infosys Springboard: Power Systems & Automation",
            "provider": "Infosys", "provider_type": "Infosys",
            "description": "Foundational training course covering electrical grid operation, power distribution, and PLC fundamentals.",
            "official_url": "https://infyspringboard.onwingspan.com/",
            "difficulty": "BEGINNER", "estimated_hours": 25, "semester_num": 3,
            "skills": [("Power Systems", "BEGINNER"), ("PLC Programming", "BEGINNER")],
            "prereqs": [
                {"course_title": "Circuit Analysis Fundamentals", "min_score": 50.0},
            ],
            "exams": [
                {"name": "Infosys Power Systems Assessment", "duration": "60 mins", "score": 65.0, "pattern": "Online quiz assessment", "link": "https://infyspringboard.onwingspan.com/"},
            ],
            "benefits": [
                {"benefit": "Free accessible foundation certificate for core engineering roles", "order": 1},
            ],
        },
    ],
    "Mechanical": [
        {
            "title": "CSWA: Certified SOLIDWORKS Associate in Mechanical Design",
            "provider": "Dassault Systèmes / SolidWorks", "provider_type": "Others",
            "description": "Globally recognized industry benchmark certifying 3D part modelling, assembly creation, and engineering drawing.",
            "official_url": "https://www.solidworks.com/certifications/mechanical-design-cswa",
            "difficulty": "INTERMEDIATE", "estimated_hours": 35, "semester_num": 3,
            "skills": [("SolidWorks", "INTERMEDIATE"), ("AutoCAD", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "3D Modelling with SolidWorks", "min_score": 65.0},
            ],
            "exams": [
                {"name": "CSWA Exam", "duration": "180 mins", "score": 70.0, "pattern": "Online hands-on SolidWorks modelling exam with mass verification", "link": "https://solidworks.com/cswa"},
            ],
            "benefits": [
                {"benefit": "Globally recognized proof of SolidWorks competence", "order": 1},
                {"benefit": "Direct requirement for 70%+ mechanical design engineering job shortlists", "order": 2},
                {"benefit": "Digital certificate badge verifyable via 3DEXPERIENCE platform", "order": 3},
            ],
        },
        {
            "title": "CSWP: Certified SOLIDWORKS Professional in Mechanical Design",
            "provider": "Dassault Systèmes / SolidWorks", "provider_type": "Others",
            "description": "Advanced certification proving ability to design complex parametric parts, edit existing parts, and configure assemblies.",
            "official_url": "https://www.solidworks.com/certifications/mechanical-design-cswp",
            "difficulty": "ADVANCED", "estimated_hours": 50, "semester_num": 5,
            "skills": [("SolidWorks", "ADVANCED"), ("AutoCAD", "ADVANCED"), ("Finite Element Analysis", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "3D Modelling with SolidWorks", "min_score": 80.0},
            ],
            "exams": [
                {"name": "CSWP 3-Segment Exam", "duration": "210 mins", "score": 75.0, "pattern": "3 timed segments testing complex part modification and assembly", "link": "https://solidworks.com/cswp"},
            ],
            "benefits": [
                {"benefit": "Gold tier mechanical CAD credential worldwide", "order": 1},
                {"benefit": "High placement priority for R&D and product design engineer roles", "order": 2},
            ],
        },
        {
            "title": "Autodesk Certified Professional in AutoCAD for Design",
            "provider": "Autodesk", "provider_type": "Others",
            "description": "Validates professional mastery of advanced 2D drafting, 3D modelling, parametric constraints, and GD&T in AutoCAD.",
            "official_url": "https://www.autodesk.com/education/certification/certifications/autocad-mechanical-design-professional",
            "difficulty": "INTERMEDIATE", "estimated_hours": 30, "semester_num": 3,
            "skills": [("AutoCAD", "INTERMEDIATE"), ("CNC Machining", "BEGINNER")],
            "prereqs": [
                {"course_title": "Engineering Drawing & AutoCAD", "min_score": 60.0},
            ],
            "exams": [
                {"name": "Autodesk AutoCAD Professional Exam", "duration": "120 mins", "score": 70.0, "pattern": "Selected response and performance-based application questions", "link": "https://autodesk.com/certification"},
            ],
            "benefits": [
                {"benefit": "Official Autodesk credential for CAD draftspersons and design engineers", "order": 1},
            ],
        },
        {
            "title": "ANSYS Certified Associate: Structural Mechanics",
            "provider": "ANSYS", "provider_type": "Others",
            "description": "Certifies competence in linear static, modal, thermal, and non-linear finite element analysis using ANSYS Mechanical.",
            "official_url": "https://www.ansys.com/training-center/course-catalog/structures",
            "difficulty": "ADVANCED", "estimated_hours": 45, "semester_num": 5,
            "skills": [("Finite Element Analysis", "ADVANCED"), ("SolidWorks", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Finite Element Analysis with ANSYS", "min_score": 70.0},
            ],
            "exams": [
                {"name": "ANSYS Structural Mechanics Associate Exam", "duration": "90 mins", "score": 75.0, "pattern": "Proctored MCQs and FEA model setup evaluation", "link": "https://ansys.com"},
            ],
            "benefits": [
                {"benefit": "Highest industry value for FEA/CAE simulation analyst positions", "order": 1},
                {"benefit": "Unlocks specialized recruitment drives at aerospace and automotive OEMs", "order": 2},
            ],
        },
        {
            "title": "NPTEL: Fundamentals of Manufacturing Processes",
            "provider": "NPTEL (IIT Roorkee)", "provider_type": "NPTEL",
            "description": "12-week course on casting, joining, metal forming, machining principles, and CNC programming.",
            "official_url": "https://nptel.ac.in/courses/112/107/112107144/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 40, "semester_num": 4,
            "skills": [("CNC Machining", "INTERMEDIATE"), ("AutoCAD", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Manufacturing Processes & CNC", "min_score": 60.0},
            ],
            "exams": [
                {"name": "NPTEL Proctored Exam", "duration": "180 mins", "score": 60.0, "pattern": "Proctored MCQs and numerical manufacturing problems", "link": "https://nptel.ac.in"},
            ],
            "benefits": [
                {"benefit": "3 academic credits for mechanical engineering degree", "order": 1},
                {"benefit": "GATE Mechanical paper preparation boost", "order": 2},
            ],
        },
        {
            "title": "NVIDIA DLI: Fundamentals of Accelerated Computing with CUDA C/C++",
            "provider": "NVIDIA", "provider_type": "NVIDIA",
            "description": "Hands-on training on parallel programming on NVIDIA GPUs for high-performance mechanical CFD simulations.",
            "official_url": "https://www.nvidia.com/en-us/training/online/",
            "difficulty": "ADVANCED", "estimated_hours": 30, "semester_num": 6,
            "skills": [("Finite Element Analysis", "INTERMEDIATE"), ("MATLAB", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "Fluid Mechanics & CFD", "min_score": 65.0},
            ],
            "exams": [
                {"name": "NVIDIA CUDA Certificate Assessment", "duration": "480 mins", "score": 80.0, "pattern": "GPU kernel programming lab task in Jupyter environment", "link": "https://nvidia.com/dli"},
            ],
            "benefits": [
                {"benefit": "Specialized certificate for HPC and computational fluid dynamics engineers", "order": 1},
            ],
        },
        {
            "title": "Coursera: Autodesk Fusion 360 Integrated CAD/CAM/CAE Specialization",
            "provider": "Coursera / Autodesk", "provider_type": "Coursera",
            "description": "4-course specialization covering 3D modelling, CAM toolpath generation, CNC simulation, and generative design.",
            "official_url": "https://www.coursera.org/specializations/autodesk-fusion-360-cad-cam-cae",
            "difficulty": "INTERMEDIATE", "estimated_hours": 40, "semester_num": 4,
            "skills": [("SolidWorks", "INTERMEDIATE"), ("CNC Machining", "INTERMEDIATE")],
            "prereqs": [
                {"course_title": "3D Modelling with SolidWorks", "min_score": 60.0},
            ],
            "exams": [
                {"name": "Fusion 360 Specialization Capstone", "duration": "Self-paced", "score": 80.0, "pattern": "CAD/CAM model submission peer review + quizzes", "link": "https://coursera.org"},
            ],
            "benefits": [
                {"benefit": "Comprehensive CAD/CAM/CAE certificate for modern digital manufacturing", "order": 1},
            ],
        },
        {
            "title": "AWS Certified Developer – Associate",
            "provider": "AWS", "provider_type": "AWS",
            "description": "Demonstrates technical proficiency in developing, deploying, and debugging cloud applications for IoT connected hardware.",
            "official_url": "https://aws.amazon.com/certification/certified-developer-associate/",
            "difficulty": "INTERMEDIATE", "estimated_hours": 45, "semester_num": 5,
            "skills": [("AutoCAD", "INTERMEDIATE"), ("SolidWorks", "BEGINNER")],
            "prereqs": [
                {"course_title": "Engineering Drawing & AutoCAD", "min_score": 50.0},
            ],
            "exams": [
                {"name": "AWS DVA-C02 Exam", "duration": "130 mins", "score": 720.0, "pattern": "65 multiple choice and multiple response questions", "link": "https://aws.amazon.com"},
            ],
            "benefits": [
                {"benefit": "Cross-disciplinary cloud credential for smart product design engineers", "order": 1},
            ],
        },
        {
            "title": "Six Sigma Green Belt (SSGB) Certification",
            "provider": "Others", "provider_type": "Others",
            "description": "Certifies mastery of DMAIC methodology, statistical process control, lean manufacturing, and quality management.",
            "official_url": "https://asq.org/cert/six-sigma-green-belt",
            "difficulty": "INTERMEDIATE", "estimated_hours": 35, "semester_num": 5,
            "skills": [("CNC Machining", "INTERMEDIATE"), ("AutoCAD", "BEGINNER")],
            "prereqs": [
                {"course_title": "Manufacturing Processes & CNC", "min_score": 60.0},
            ],
            "exams": [
                {"name": "ASQ SSGB Exam", "duration": "240 mins", "score": 70.0, "pattern": "110 multiple choice questions covering DMAIC body of knowledge", "link": "https://asq.org"},
            ],
            "benefits": [
                {"benefit": "Highly requested quality engineering credential across manufacturing and automotive OEMs", "order": 1},
                {"benefit": "Substantial advantage for industrial and production engineering roles", "order": 2},
            ],
        },
        {
            "title": "Infosys Springboard: Mechanical Design & CAD Automation",
            "provider": "Infosys", "provider_type": "Infosys",
            "description": "Industry training path covering mechanical engineering fundamentals, 3D modelling, and automated drafting.",
            "official_url": "https://infyspringboard.onwingspan.com/",
            "difficulty": "BEGINNER", "estimated_hours": 25, "semester_num": 3,
            "skills": [("AutoCAD", "INTERMEDIATE"), ("SolidWorks", "BEGINNER")],
            "prereqs": [
                {"course_title": "Engineering Drawing & AutoCAD", "min_score": 50.0},
            ],
            "exams": [
                {"name": "Infosys Mechanical CAD Assessment", "duration": "60 mins", "score": 65.0, "pattern": "Online MCQs and CAD quiz", "link": "https://infyspringboard.onwingspan.com/"},
            ],
            "benefits": [
                {"benefit": "Free accessible foundation certificate for engineering design roles", "order": 1},
            ],
        },
    ],
}
