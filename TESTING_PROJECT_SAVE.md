# Testing Project Data Save Functionality

## Quick Test Steps

### 1. Start the Development Server

```bash
cd frontend
npm run dev
```

The app should be available at `http://localhost:8080` (or the port shown in terminal)

### 2. Navigate to New Project Page

1. Open your browser and go to `http://localhost:8080`
2. Navigate to **"Create New Project"** (usually at `/app/projects/new`)
3. Or click the "New Project" button if available

### 3. Fill Out the Form (Minimal Test)

**Required:**
- **Company Search**: Type a company name or ticker (e.g., "AAPL" or "Apple")
- Select a company from the dropdown

**Optional (for full test):**
- Fill in some Income Statement assumptions (Revenue Growth, Gross Margin, etc.)
- Fill in some DCF assumptions (Beta, Market Risk Premium, etc.)
- Add some competitors in Relative Valuation

### 4. Click "Finish" or "Generate Valuation" Button

This should trigger the save functionality.

### 5. Verify the Save Worked

#### Check 1: JSON File Download
- Check your browser's **Downloads folder**
- You should see a file named: `project_[timestamp]_[ticker].json`
- Example: `project_1704123456789_AAPL.json`

#### Check 2: Open the JSON File
- Open the downloaded JSON file in a text editor
- Verify it contains:
  - `projectId`
  - `createdAt` and `updatedAt` timestamps
  - `company` object with name and ticker
  - `incomeStatement` object with your inputs
  - `dcf` object with DCF assumptions
  - All other sections you filled out

#### Check 3: Check Browser Console
- Open browser DevTools (F12)
- Go to **Console** tab
- Look for any error messages
- Should see success message: "Project created and saved successfully!"

#### Check 4: Check localStorage
- In DevTools, go to **Application** tab (Chrome) or **Storage** tab (Firefox)
- Expand **Local Storage** → `http://localhost:8080`
- Look for key: `denari_projects`
- Click on it to see the saved project data

### 6. Test Loading Saved Projects

You can test loading the saved data by checking the browser console:

```javascript
// In browser console, run:
const { getSavedProjects } = await import('/src/lib/saveProjectData.ts');
// Actually, better to test via the UI or create a test page
```

Or check localStorage directly:
```javascript
// In browser console:
JSON.parse(localStorage.getItem('denari_projects'))
```

## Expected JSON Structure

The saved JSON should look like this:

```json
{
  "projectId": "project_1704123456789_AAPL",
  "createdAt": "2024-01-01T12:00:00.000Z",
  "updatedAt": "2024-01-01T12:00:00.000Z",
  "company": {
    "name": "Apple Inc.",
    "ticker": "AAPL"
  },
  "incomeStatement": {
    "revenue": {
      "method": "step",
      "stepValue": "5"
    },
    "grossMargin": {
      "method": "stable",
      "stableValue": "40"
    }
  },
  "dcf": {
    "beta": {
      "method": "manual",
      "value": "1.2"
    },
    "marketRiskPremium": "6.0",
    "riskFreeRate": "2.5",
    "terminalGrowthRate": "2.5",
    "scenario": "bear"
  },
  "relativeValuation": {
    "competitors": ["MSFT", "GOOGL"]
  }
  // ... more sections
}
```

## Troubleshooting

### Issue: No file downloads
- **Check**: Browser download settings (may be blocked)
- **Check**: Browser console for errors
- **Solution**: Check browser's download permissions

### Issue: localStorage not saving
- **Check**: Browser console for errors
- **Check**: If you're in incognito/private mode (localStorage may be restricted)
- **Solution**: Use regular browsing mode

### Issue: JSON file is empty or malformed
- **Check**: Browser console for errors
- **Check**: Make sure you selected a company before clicking finish
- **Solution**: Fill out at least the company selection

### Issue: "Failed to save project" error
- **Check**: Browser console for detailed error
- **Check**: Make sure all required fields are filled
- **Solution**: Verify the `saveProjectData.ts` file exists and is imported correctly

## Advanced Testing

### Test with Different Scenarios

1. **Minimal Data**: Only select company, leave everything else empty
2. **Full Data**: Fill out all sections completely
3. **Bear Scenario**: Set scenario to "bear" and fill bear assumptions
4. **Bull Scenario**: Set scenario to "bull" and fill bull assumptions
5. **Manual vs Stable**: Test different input methods (stable, step, manual)

### Test Excel Format Function

You can test the Excel formatting function in the browser console:

```javascript
// After saving a project, in console:
const projectData = JSON.parse(localStorage.getItem('denari_projects'))[0];
const { formatProjectDataForExcel } = await import('/src/lib/saveProjectData.ts');
const excelData = formatProjectDataForExcel(projectData);
console.log(excelData);
```

This will show you the flattened structure ready for Excel export.

## Next Steps

Once you've verified the save works:
1. The JSON file can be sent to your backend API
2. The backend can use this data to generate financial models
3. You can use `formatProjectDataForExcel()` to export to Excel later

