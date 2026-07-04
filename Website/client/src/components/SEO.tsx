/**
 * SEO Component
 * Uses react-helmet-async to dynamically update <head> tags per page.
 * This helps search engines and social media crawlers get page-specific metadata.
 */
import { Helmet } from "react-helmet-async";

interface SEOProps {
  title: string;
  description: string;
  canonical?: string;
  ogImage?: string;
  ogType?: string;
  keywords?: string;
  noindex?: boolean;
}

const BASE_URL = "https://www.pp5mediasolutions.com";
const DEFAULT_OG_IMAGE = `${BASE_URL}/favicon.png`;
const SITE_NAME = "PP5 Media Solutions";

/**
 * Reusable SEO head tag manager.
 * Place at the top of each page component to set page-specific metadata.
 *
 * @example
 * <SEO
 *   title="Services | PP5 Media Solutions"
 *   description="Explore our creative and digital services..."
 * />
 */
export function SEO({
  title,
  description,
  canonical,
  ogImage = DEFAULT_OG_IMAGE,
  ogType = "website",
  keywords,
  noindex = false,
}: SEOProps) {
  const fullTitle = title.includes(SITE_NAME)
    ? title
    : `${title} | ${SITE_NAME}`;

  const canonicalUrl = canonical
    ? `${BASE_URL}${canonical}`
    : undefined;

  return (
    <Helmet>
      {/* Primary */}
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      {keywords && <meta name="keywords" content={keywords} />}
      {canonicalUrl && <link rel="canonical" href={canonicalUrl} />}
      {noindex && <meta name="robots" content="noindex, nofollow" />}

      {/* Open Graph */}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content={ogType} />
      <meta property="og:image" content={ogImage} />
      {canonicalUrl && <meta property="og:url" content={canonicalUrl} />}
      <meta property="og:site_name" content={SITE_NAME} />

      {/* Twitter Card */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />
    </Helmet>
  );
}
