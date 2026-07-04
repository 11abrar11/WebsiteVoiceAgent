
export interface CaseStudy {
    id: string;
    slug: string;
    title: string;
    client: string;
    category: string;
    description: string;
    theAsk: string;
    solutionIntro: string;
    solutionPoints: string[];
    results: string[];
    image: string; // Hero image
    gallery?: string[];
}

export const caseStudies: CaseStudy[] = [
    {
        id: '1',
        slug: 'dfw-airport-parking',
        title: 'Creative Marketing Collateral for DFW Airport Parking',
        client: 'DFW Airport Parking (via ABI - Alpha Business Images)',
        category: 'Digital Banners & Motion Graphics',
        description: 'A series of highly engaging static and animated marketing collateral for one of the largest and busiest airport parking facilities in the United States — delivered at scale with a fast turnaround.',
        theAsk: 'The client, ABI (Alpha Business Images), approached PP5 Media Solutions to develop a series of highly engaging marketing collateral for DFW Airport Parking. The requirement included static and animated digital banners, creative assets for seasonal promotions, loyalty campaigns, and limited-time offers — all aligned with DFW\'s brand guidelines while maintaining high visual impact and consistency across channels, with fast turnaround to meet time-sensitive campaign launches.',
        solutionIntro: 'PP5 Media Solutions assembled a dedicated creative team of designers and motion graphic specialists to deliver a seamless experience:',
        solutionPoints: [
            'Brand Deep-Dive: Studied DFW\'s branding guidelines and past campaigns to ensure alignment with tone, color palette, and messaging.',
            'Design Execution: Produced a suite of static banners, GIFs, and animated HTML5 banners optimized for performance across web and mobile platforms.',
            'Agile Collaboration: Maintained a 24×5 communication channel with the ABI (Alpha Business Images) team via email, Skype, and shared cloud folders to enable real-time feedback and revisions.',
            'Quality Assurance: Conducted thorough design and animation quality checks to ensure pixel-perfect output and cross-platform compatibility.',
        ],
        results: [
            '400+ creative assets delivered across multiple campaign cycles',
            'Significant boost in click-through rates (CTR) vs. previous static creatives',
            'Client praised turnaround time, visual creativity, and quality of execution',
            'Ongoing retainership secured after initial campaign success',
        ],
        image: '/dfw_case_study_hero.png',
        gallery: [
            '/portfolio/optimized/banners/DD.jpg',
            '/portfolio/optimized/banners/d.jpg',
            '/portfolio/optimized/banners/banner1.jpg',
            '/portfolio/optimized/social/DFW_Christmas_600x600.gif',
        ],
    },
    {
        id: '2',
        slug: 'goodwill-dallas',
        title: 'Empowering Social Impact Through Creative Campaigns',
        client: 'Goodwill Dallas',
        category: 'Print, Video & Campaign Design',
        description: 'A holistic creative strategy for Goodwill Dallas — the first Goodwill organization in Texas — to elevate the visibility and impact of its awareness and fundraising campaigns through print, digital, and video production.',
        theAsk: 'Goodwill Dallas approached PP5 Media Solutions with the need for creative design and production support to elevate the visibility and impact of its awareness and fundraising campaigns. Their goals included designing print and banner materials for community outreach, events, and retail stores; creating professional, emotionally resonant videos to support donation drives and program visibility; aligning all creative assets with their mission-driven messaging and brand identity; and enhancing engagement with both donors and community stakeholders.',
        solutionIntro: 'PP5 Media Solutions responded with a holistic creative strategy designed to drive engagement, build trust, and visually communicate Goodwill Dallas\'s impact:',
        solutionPoints: [
            'Print Design: Developed flyers, brochures, posters, and other collateral for both in-store and community use — featuring strong visuals, clear calls-to-action, and inclusive messaging.',
            'Banner Design: Created eye-catching static and digital banners for events, donation centers, and social campaigns, ensuring consistency across platforms and physical spaces.',
            'Video Production: Produced professional, high-quality videos that highlighted personal success stories, donor impact, and community initiatives — key tools in donor outreach and digital marketing.',
            'Collaborative Workflow: Maintained close coordination with the Goodwill Dallas team to ensure each asset reflected their mission, values, and strategic objectives.',
        ],
        results: [
            'Campaign videos and materials significantly improved donor response',
            'Enhanced branding reinforced Goodwill\'s presence and credibility in the local community',
            'Professional designs aligned with their long-term vision for 2030',
            'Ongoing collaboration and creative support secured after initial campaign success',
        ],
        image: '/goodwill_case_study_hero.png',
        gallery: [
            '/portfolio/optimized/social/23.png',
            '/portfolio/optimized/banners/Coverpage.jpg',
            '/portfolio/optimized/eblast/eblast1.gif',
            '/portfolio/optimized/flyers/Goodwill_02_JPFeedback.pdf',
        ],
    },
];
