# Project Data Storage Guide

## Where Does the JSON Live?

When you create a new project, the JSON data is **saved to browser localStorage** (not downloaded as a file).

### Storage Location

- **Browser localStorage** under the key: `denari_projects`
- **Location**: Browser's local storage (persists across sessions)
- **Access**: Available immediately after project creation
- **No download**: The file is NOT downloaded to your computer

## How to Access the Data for Excel Export

### Option 1: Get Latest Project (Recommended)

Use this when you want to export the most recently created project:

```typescript
import { getLatestProjectFormattedForExcel } from "@/lib/loadProjectForExcel";

const handleExport = async () => {
  const projectData = getLatestProjectFormattedForExcel();
  
  if (!projectData) {
    toast.error("No project data found. Please create a project first.");
    return;
  }
  
  // Use projectData in your Excel export
  // projectData contains all assumptions:
  // - projectData.revenueMethod
  // - projectData.revenueStableValue
  // - projectData.betaValue
  // - projectData.marketRiskPremium
  // - etc.
}
```

### Option 2: Get Project by ID

Use this when you know the specific project ID:

```typescript
import { getProjectDataByIdForExcel, formatProjectForExcel } from "@/lib/loadProjectForExcel";

const projectId = "project_1704123456789_AAPL";
const project = getProjectDataByIdForExcel(projectId);
const formattedData = formatProjectForExcel(project);
```

### Option 3: Get Project by Ticker

Use this when you know the company ticker:

```typescript
import { getProjectDataByTickerForExcel, formatProjectForExcel } from "@/lib/loadProjectForExcel";

const project = getProjectDataByTickerForExcel("AAPL");
const formattedData = formatProjectForExcel(project);
```

### Option 4: Get All Projects

Use this to list all saved projects:

```typescript
import { getSavedProjects } from "@/lib/saveProjectData";

const allProjects = getSavedProjects();
// Returns array of all ProjectData objects
```

## Data Structure

The project data is stored as a structured JSON object with:

- **Project metadata**: `projectId`, `createdAt`, `updatedAt`
- **Company info**: `company.name`, `company.ticker`
- **Income Statement assumptions**: Revenue, Gross Margin, Operating Margin, Tax Rate
- **Balance Sheet assumptions**: Depreciation, Total Debt, Inventory, etc.
- **Cash Flow assumptions**: Share Repurchases, Dividends, CAPEX, Change in WC
- **DCF assumptions**: Beta, Market Risk Premium, Risk-Free Rate, Terminal Growth Rate
- **Bear/Bull scenarios**: All scenario-specific assumptions
- **Relative Valuation**: Competitors list

## Example: Using in Excel Export

Here's how you would use it in your Excel export function:

```typescript
import { getLatestProjectFormattedForExcel } from "@/lib/loadProjectForExcel";
import { downloadExcelFromTemplate } from "@/lib/downloadExcel";

const handleExport = async () => {
  try {
    // Get the latest project data
    const projectData = getLatestProjectFormattedForExcel();
    
    if (!projectData) {
      toast.error("No project data found. Please create a project first.");
      return;
    }
    
    // Build your Excel data map using project data
    const dataMap: Record<string, any> = {
      'B2': projectData.companyName,
      'J2': projectData.ticker,
      'J5': new Date(),
      // Use project assumptions
      'D17': projectData.revenueYear1,
      'D18': projectData.grossMarginYear1,
      // ... etc
    };
    
    // Export to Excel
    await downloadExcelFromTemplate(
      '/Templates/DCF_A_Template.xlsx',
      dataMap,
      `${projectData.ticker}-model`
    );
  } catch (error) {
    console.error('Export failed:', error);
    toast.error('Failed to export Excel file.');
  }
};
```

## Checking localStorage (Browser DevTools)

You can verify the data is stored by:

1. Open browser DevTools (F12)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Expand **Local Storage** → `http://localhost:8080`
4. Look for key: `denari_projects`
5. Click to see the JSON data

## Important Notes

- **localStorage is per-domain**: Data is stored per browser/domain
- **Storage limit**: ~5-10MB per domain (plenty for project data)
- **Persistence**: Data persists until user clears browser data
- **No backend required**: Data lives entirely in the browser
- **Multiple projects**: All projects are stored in an array under `denari_projects`

## For Backend Integration

If you want to send the data to your backend:

```typescript
import { getLatestProject } from "@/lib/saveProjectData";

const projectData = getLatestProject();
if (projectData) {
  // Send to backend API
  const response = await fetch('/api/v1/models/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(projectData)
  });
}
```

The backend can then use this JSON to generate the financial model and Excel file.

