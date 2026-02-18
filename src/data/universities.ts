export const TOP_US_UNIVERSITIES = [
  // Ivy League
  'Harvard University',
  'Yale University',
  'Princeton University',
  'Columbia University',
  'University of Pennsylvania',
  'Brown University',
  'Dartmouth College',
  'Cornell University',
  
  // Top Public Universities
  'University of California, Berkeley',
  'University of California, Los Angeles (UCLA)',
  'University of Michigan',
  'University of Virginia',
  'University of North Carolina at Chapel Hill',
  'University of Florida',
  'University of Texas at Austin',
  'University of Wisconsin-Madison',
  'University of Washington',
  'Georgia Institute of Technology',
  'University of Illinois Urbana-Champaign',
  'Ohio State University',
  'Pennsylvania State University',
  'Purdue University',
  'University of Maryland',
  'University of Minnesota',
  'Rutgers University',
  'University of Pittsburgh',
  
  // Top Private Universities
  'Stanford University',
  'Massachusetts Institute of Technology (MIT)',
  'Duke University',
  'Northwestern University',
  'University of Chicago',
  'Johns Hopkins University',
  'California Institute of Technology (Caltech)',
  'Rice University',
  'Vanderbilt University',
  'Washington University in St. Louis',
  'Emory University',
  'Georgetown University',
  'Carnegie Mellon University',
  'University of Southern California',
  'New York University',
  'Boston University',
  'Tufts University',
  'Wake Forest University',
  
  // More UC Schools
  'University of California, San Diego',
  'University of California, Davis',
  'University of California, Santa Barbara',
  'University of California, Irvine',
  'University of California, Riverside',
  'University of California, Santa Cruz',
  'University of California, Merced',
  
  // Other Notable Universities
  'University of Notre Dame',
  'University of Miami',
  'Boston College',
  'Northeastern University',
  'Syracuse University',
  'University of Rochester',
  'Case Western Reserve University',
  'Tulane University',
  'Lehigh University',
  'Rensselaer Polytechnic Institute',
  'Worcester Polytechnic Institute',
  'University of Connecticut',
  'University of Delaware',
  'George Washington University',
  'American University',
  'Howard University',
  'Spelman College',
  'Morehouse College',
  
  // Other input option
  'Other'
];

export const searchUniversities = (query: string): string[] => {
  if (!query) return TOP_US_UNIVERSITIES.slice(0, 10);
  
  const lowerQuery = query.toLowerCase();
  return TOP_US_UNIVERSITIES.filter(uni => 
    uni.toLowerCase().includes(lowerQuery)
  ).slice(0, 20);
};
