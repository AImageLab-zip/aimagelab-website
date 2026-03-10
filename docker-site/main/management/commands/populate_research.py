from django.core.management.base import BaseCommand
from main.models import HistoryMilestone, ResearchArea


class Command(BaseCommand):
    help = 'Populate HistoryMilestone and ResearchArea tables with default content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing milestones and research areas before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            HistoryMilestone.objects.all().delete()
            ResearchArea.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing data.'))

        # ── History Milestones ──────────────────────────────────────────
        milestones = [
            {
                'year_label': '1999',
                'title': 'Foundation',
                'icon': 'flag',
                'description': (
                    'Founded by Prof. Rita Cucchiara, initially focused on image processing and computer '
                    'vision, later expanding to applied AI.'
                ),
                'display_order': 10,
            },
            {
                'year_label': '2000s',
                'title': 'Scientific Growth',
                'icon': 'trending-up',
                'description': (
                    'Expanded into video understanding, multimedia analytics, and human\u2013machine interaction, '
                    'becoming one of Italy\'s leading AI groups with international collaborations.'
                ),
                'display_order': 20,
            },
            {
                'year_label': '2016',
                'title': 'International Recognition',
                'icon': 'globe',
                'description': (
                    'Selected by Facebook AI Research among 15 EU labs for a strategic GPU partnership.'
                ),
                'display_order': 30,
            },
            {
                'year_label': '2018',
                'title': 'Joined AIRI',
                'icon': 'building',
                'description': (
                    'Joined AIRI (formerly Softech), interdepartmental AI center accredited by the Emilia Romagna '
                    'High Technology Network; initiated the founding collection for the new building; launched AI '
                    'for health/bioinformatics through the EU projects DeepHealth and Decider.'
                ),
                'display_order': 40,
            },
            {
                'year_label': '2020',
                'title': 'NVIDIA AI Technology Center',
                'icon': 'cpu',
                'description': (
                    'Became host of the NVIDIA AI Technology Center (NVAITC) at the Modena Technopole.'
                ),
                'display_order': 50,
            },
            {
                'year_label': '2021',
                'title': 'ELLIS Unit Appointment',
                'icon': 'globe',
                'description': (
                    'Appointed as an ELLIS Unit within the European AI network; participated in EU projects '
                    '(ELISE, ELSA, ELIAS, ELLIOT); promoted the ELLIS Summer School in AI and HPC.'
                ),
                'display_order': 60,
            },
            {
                'year_label': '2022\u20132023',
                'title': 'PNRR Projects',
                'icon': 'file-text',
                'description': (
                    'Partecipated in PNRR projects (ITSERR, Ecosister, Fit4MedRob, FAIR as a CNR unit).'
                ),
                'display_order': 70,
            },
            {
                'year_label': '2025',
                'title': 'EuroHPC',
                'icon': 'zap',
                'description': (
                    'Won the EuroHPC Extreme Scale call for frontier Large-Scale AI research and projects.'
                ),
                'display_order': 80,
            },
        ]

        for m in milestones:
            obj, created = HistoryMilestone.objects.update_or_create(
                year_label=m.pop('year_label'),
                title=m.pop('title'),
                defaults=m,
            )
            status = 'created' if created else 'updated'
            self.stdout.write(f'  Milestone {obj.year_label} \u2014 {obj.title}: {status}')

        # ── Research Areas ──────────────────────────────────────────────
        areas = [
            {
                'area_id': 'multimodal-ai',
                'title': 'Large-Scale Multimodal AI',
                'icon': 'images',
                'color': 'primary',
                'homepage_caption': (
                    'Development of large-scale multimodal architectures for visual question answering, '
                    'grounded language generation, image editing understanding, and generative AI. '
                    'Foundation model research, with access to EuroHPC-scale infrastructure.'
                ),
                'intro': (
                    'Our Multimodal AI group develops large-scale architectures that bridge visual perception '
                    'and natural language understanding, with a focus on trustworthy and deployable AI solutions. '
                    'We design joint representation models over images, video, and text to support tasks such as '
                    'visual question answering, dense captioning, cross-modal retrieval, and zero-shot recognition. '
                    'The group is active within the ELLIS network through EU projects ELIAS, ELSA, and ELLIOT, '
                    'and collaborates with CINECA on large-scale training infrastructure \u2013 including access '
                    'granted through a competitive win of the EuroHPC Extreme Scale Access Call.'
                ),
                'detail': (
                    'Key research threads include reasoning-augmented and retrieval-augmented generation for '
                    'knowledge-intensive visual tasks, hallucination mitigation in multimodal large language '
                    'models via preference optimization, missing-modality robustness in multimodal pipelines, '
                    'and instruction-guided image edit detection and evaluation. We also advance generative AI '
                    'for structured visual content, including scalable vector graphics generation through large '
                    'language models, and inference-time scaling strategies for video diffusion models. The core '
                    'mission is to push multimodal foundation models toward grounded, interpretable, and reliable '
                    'reasoning, bridging the gap between research prototypes and real-world deployment across '
                    'vision-language applications.'
                ),
                'keywords': (
                    'visual-qa,multimodal-llm,hallucination-mitigation,grounded-generation,'
                    'retrieval-augmented-generation,image-editing,vector-graphics-generation,'
                    'video-diffusion,foundation-models'
                ),
                'display_order': 10,
            },
            {
                'area_id': 'ml-dl',
                'title': 'Machine Learning & Deep Learning',
                'icon': 'waypoints',
                'color': 'secondary',
                'homepage_caption': (
                    'Development of novel algorithms and architectures for supervised, unsupervised, and '
                    'reinforcement learning, federated learning, model merging, and PEFT. Model maintenance '
                    'and incremental update techniques for efficient deep learning solutions.'
                ),
                'intro': (
                    'Our ML/DL group develops the foundational algorithms and training methodologies that '
                    'power every project in the lab. We design novel neural architectures, study generalisation '
                    'theory, and build robust training pipelines for both computer-vision, language and time '
                    'series industrial tasks'
                ),
                'detail': (
                    'Key research threads include continual learning and catastrophic-forgetting mitigation, '
                    'incremental learning and model updates, neural architecture search (NAS), parameter-efficient '
                    'fine-tuning (PEFT), model merging and ensemble strategies, self-supervised pretraining on '
                    'unlabelled data and novel online learning strategies. We also contribute to the reliability '
                    'and interpretability of deep models, studying calibration, uncertainty estimation, and '
                    'feature attribution methods. The core mission is to provide technical and theoretical '
                    'foundation for the resilience, the management and the life cycle of modern deep learning '
                    'solutions incorporating learning strategies into the model inference and creating modular '
                    'solutions that can be modified without altering the base model architecture. The studied '
                    'techniques are the cornerstone of post deployment model resilience allowing to bridge the '
                    'gap between prototypes and laboratory research and actual real life products.'
                ),
                'keywords': (
                    'continual-learning,neural-architecture-search,peft,model-merging,'
                    'self-supervised-learning,uncertainty-estimation'
                ),
                'display_order': 20,
            },
            {
                'area_id': 'medical-imaging',
                'title': 'Medical Imaging',
                'icon': 'microscope',
                'color': 'success',
                'homepage_caption': (
                    'Deep Learning for Medical Image Analysis and Clinically Deployable Decision Support.'
                ),
                'intro': (
                    'We develop robust and reproducible AI methods for medical imaging, spanning 2D '
                    '(e.g., ultrasounds and dermoscopy) and 3D volumetric analysis (e.g., CBCT and MRI) '
                    'and computational pathology. The research combines model design, rigorous benchmarking, '
                    'and efficient algorithms to enable reliable evaluation and transferability across clinical '
                    'sites and acquisition settings.'
                ),
                'detail': (
                    'Ongoing projects include automated segmentation in complex 3D scans\u2014such as '
                    'maxillofacial structures and neurovascular anatomy in CBCT\u2014together with multimodal '
                    'brain tumour segmentation under missing-modality conditions and large-scale evaluation on '
                    'community benchmarks (e.g., BraTS). The group also develops learning-based pipelines for '
                    'ultrasound and other routine clinical modalities, targeting tasks such as detection, '
                    'grading, and quantitative measurement under real-world acquisition variability. Additional '
                    'work investigates computer vision methods for clinical analysis of facial behaviour, '
                    'including automatic detection of facial muscle weakness and neurological conditions through '
                    'video-based analysis. Clinical applicability is the driving force throughout: methods are '
                    'designed to be robust across centres and devices, label-efficient, and interpretable, with '
                    'validation protocols aligned with clinical workflows and regulatory constraints. To foster '
                    'reproducible research and push research boundaries, the group actively contributes to data '
                    'collection and public release\u2014organizing international challenges whenever '
                    'possible\u2014and studies synthetic medical image generation to augment scarce data, probe '
                    'failure modes, and improve generalization.'
                ),
                'keywords': 'Segmentation,Benchmarking,Synthetic Image Generation,Multimodal Fusion,Missing Modalities',
                'display_order': 30,
            },
            {
                'area_id': 'computer-vision',
                'title': 'Computer Vision',
                'icon': 'aperture',
                'color': 'primary',
                'homepage_caption': (
                    'Advanced algorithms for image and video analysis, object recognition, and scene understanding.'
                ),
                'intro': (
                    'Computer Vision is the heart of AImageLab. Our researchers tackle the full visual '
                    'understanding stack: low-level image restoration and enhancement, mid-level structural '
                    'recognition, and high-level semantic scene understanding for images and video in the '
                    'multimodal AI era.'
                ),
                'detail': (
                    'We are particularly active in action recognition, video object segmentation, pedestrian '
                    're-identification, 3D scene reconstruction, and generative modelling and editing (flow '
                    'matching models, diffusion models, GANs). Our video understanding work targets both '
                    'efficiency \u2014 enabling real-time inference on edge hardware \u2014 and accuracy, '
                    'pushing state-of-the-art on international benchmarks such as ActivityNet, MOT, and '
                    'Market-1501. We also study flexible multimodal open vocabulary solutions for fundamental '
                    'computer vision problems stemming from object detection, segmentation, tracking and 3D '
                    'reconstruction by leveraging the most advanced multimodal open vocabulary architectures '
                    'and fostering efficient large scale training and modular AI solutions tailored for fine '
                    'grained vision tasks. Another research direction focuses on modelling human visual '
                    'attention through eye-movement analysis, including prediction and generative modelling '
                    'of gaze scanpaths from images and videos, as well as the analysis of egocentric visual '
                    'data collected with wearable eye-tracking devices.'
                ),
                'keywords': (
                    'action-recognition,re-identification,object-detection,3d-reconstruction,'
                    'diffusion-models,video-understanding,visual-attention,gaze-modelling'
                ),
                'display_order': 40,
            },
            {
                'area_id': 'iot-embedded',
                'title': 'IoT & Embedded AI',
                'icon': 'wifi-cog',
                'color': 'warning',
                'homepage_caption': (
                    'Research and Design on advanced IoT systems, embedded AI and sensor integration.'
                ),
                'intro': (
                    'We design end-to-end systems that fuse data from heterogeneous sensor networks \u2014 '
                    'RGB cameras, IMUs, event and depth cameras, LiDARs, and any type of connected sensors '
                    '\u2014 to enable pervasive, context-aware intelligence at the edge.'
                ),
                'detail': (
                    'Our embedded AI research targets microcontroller and AI accelerator deployment of Machine '
                    'Learning algorithms, tackling the trade-off between model accuracy and resource footprint '
                    'with quantisation, pruning, and knowledge distillation. Use cases span from Monocular '
                    'Depth Estimation, precision agriculture, Industrial IoT, and wearable health-sensing '
                    'platforms.'
                ),
                'keywords': 'Embedded AI,model-compression,sensor-fusion,TinyML,AI on microcontrollers',
                'display_order': 50,
            },
            {
                'area_id': 'robotics-hri',
                'title': 'Robotics & Human-Robot Interaction',
                'icon': 'bot',
                'color': 'error',
                'homepage_caption': (
                    'Human-robot interaction, Embodied AI and autonomous systems for real-world applications.'
                ),
                'intro': (
                    'We create autonomous systems capable of perceiving, understanding, and acting in complex '
                    'human environments. Our robots learn from human demonstrations, adapt to novel scenarios '
                    'through sim-to-real transfer, and communicate intuitively with people. We also develop '
                    'Embodied AI algorithms that enable agents to navigate and reason in 3D environments, '
                    'including language-guided navigation where agents follow natural language instructions '
                    'to reach goals.'
                ),
                'detail': (
                    'Research themes include vision-based manipulation, social navigation with pedestrian '
                    'intent prediction, multimodal dialogue systems for assistive robotics, and egocentric '
                    'action anticipation from wearable cameras. A research direction is also the development '
                    'of Vision-Language-Action (VLA) models that tightly integrate visual perception, language '
                    'understanding, and motor control into unified architectures for embodied agents. We '
                    'participate in international competitions and collaborate with industry partners on '
                    'warehouse automation and collaborative assembly applications.'
                ),
                'keywords': (
                    'sim-to-real,manipulation,social-navigation,egocentric-vision,assistive-robotics,'
                    'action-anticipation,robot-to-robot-interaction,embodied-ai,language-guided-navigation,'
                    'vision-language-action'
                ),
                'display_order': 60,
            },
            {
                'area_id': 'bioinformatics',
                'title': 'Bioinformatics and AI for Precision Medicine',
                'icon': 'dna',
                'color': 'success',
                'homepage_caption': (
                    'Bioinformatics, Computational Biology, and Multimodal Data Integration for Precision Medicine.'
                ),
                'intro': (
                    'We develop AI methods in bioinformatics and computational biology centered on multimodal '
                    'integration for precision medicine. Our models jointly learn from molecular data\u2014'
                    'including genomics, gene expression, mutational and proteomic profiles, and three-dimensional '
                    'structures\u2014together with whole slide imaging features and electronic health records, '
                    'medical charts, and visit transcripts, enabling therapy response prediction, patient '
                    'stratification, and advanced therapeutic strategies including ATMPs.'
                ),
                'detail': (
                    'Our work spans bioinformatics and computational biology, combining sequence analysis, '
                    'molecular network modeling, structural biology representations, and clinical data science '
                    'within coherent multimodal systems. DNA, RNA, and protein sequences are analyzed to identify '
                    'regulatory and mutational patterns, while gene expression dynamics, transcriptional regulation, '
                    'methylation landscapes, protein\u2013protein interaction networks, and three-dimensional '
                    'structural information are incorporated into system-level representations through reproducible '
                    'bioinformatics workflows. Quantitative information extracted from whole slide images is '
                    'integrated as one component of the broader multimodal modeling strategy, alongside molecular '
                    'and clinical variables. Our frameworks explicitly address high-dimensional, heterogeneous, '
                    'and partially observed omics and clinical data, including the management of missing modalities '
                    'and automated information extraction from clinical texts, medical records, and visit '
                    'transcripts. Through systematic data integration across molecular, imaging, and clinical '
                    'sources, we aim to enhance patient stratification, quantify and predict therapeutic response, '
                    'support precision oncology and advanced therapies, and strengthen clinical decision-making '
                    'processes through interpretable and robust AI methodologies.'
                ),
                'keywords': (
                    'Bioinformatics,Computational Biology,Multimodal Data Integration,Precision Medicine,'
                    'Genomics,Proteomics,Whole Slide Imaging,Electronic Health Records,Clinical Text Mining,'
                    'Therapy Response Prediction,ATMPs,Missing Modalities'
                ),
                'display_order': 70,
            },
        ]

        for a in areas:
            area_id = a.pop('area_id')
            obj, created = ResearchArea.objects.update_or_create(
                area_id=area_id,
                defaults=a,
            )
            status = 'created' if created else 'updated'
            self.stdout.write(f'  Research area {obj.area_id} \u2014 {obj.title}: {status}')

        self.stdout.write(self.style.SUCCESS(
            f'Done: {len(milestones)} milestones, {len(areas)} research areas.'
        ))
