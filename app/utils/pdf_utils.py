

from datetime import datetime
from PIL import Image
from io import  BytesIO


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import inch
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 50



# Draw page border
def draw_border(pdf):
    pdf.setStrokeColor(colors.black)
    pdf.rect(MARGIN, MARGIN, PAGE_WIDTH - 2 * MARGIN, PAGE_HEIGHT - 2 * MARGIN)

# Add Sigma header
def add_sigma_header(pdf):
    import os
    from pathlib import Path
    
    # Get absolute path to the image relative to the project root
    base_dir = Path(__file__).resolve().parent.parent.parent  # Navigate to project root
    sigma_url = os.path.join(base_dir, "static", "images", "head.jpg")
    
    try:
        sigma_img = Image.open(sigma_url)
    except FileNotFoundError:
        # Fallback to create a blank image if the header image is not found
        sigma_img = Image.new('RGB', (500, 75), color=(255, 255, 255))
    
    # Calculate image dimensions and positions
    img_width = PAGE_WIDTH - 2 * MARGIN
    img_height = 75
    img_x = MARGIN
    img_y = PAGE_HEIGHT - MARGIN - img_height

    # Draw black border (slightly larger than the image)
    border_thickness = 2
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(border_thickness)
    pdf.rect(img_x - border_thickness / 2, img_y - border_thickness / 2, img_width + border_thickness, img_height + border_thickness)

    # Draw the image
    pdf.drawInlineImage(sigma_img, img_x, img_y, width=img_width, height=img_height)

async def add_charts(pdf, from_date, to_date, db):
    
    cursor = db.dataset.find(
            {"ISODateTime": {
                    "$gte": from_date.isoformat(),  # Convert `from_date` to ISO 8601 format
                    "$lte": to_date.isoformat(),   # Convert `to_date` to ISO 8601 format
                }})
    issues = await cursor.to_list(length=None)

    # Initialize counters
    categories = {}
    open_issues_count = 0
    closed_issues_count = 0

    for issue in issues:
        category = issue["issue"].get("issueCat", "Unknown")
        status = issue.get("status", "Unknown")

        # Count open and closed issues
        if status == "OPEN":
            open_issues_count += 1
        elif status == "CLOSE":
            closed_issues_count += 1

        # Count issues by category
        if category not in categories:
            categories[category] = {"open": 0, "closed": 0}
        if status == "OPEN":
            categories[category]["open"] += 1
        elif status == "CLOSE":
            categories[category]["closed"] += 1

    # Prepare data for charts
    category_names = list(categories.keys())
    open_issues = [categories[cat]["open"] for cat in category_names]
    closed_issues = [categories[cat]["closed"] for cat in category_names]

    # --- Bar Chart ---
    fig, ax = plt.subplots(figsize=(5, 2))
    bar_width = 0.4
    x = range(len(category_names))

    ax.bar(x, open_issues, width=bar_width, label="Open Issues", color="orange")
    ax.bar([p + bar_width for p in x], closed_issues, width=bar_width, label="Closed Issues", color="blue")

    ax.set_xticks([p + bar_width / 2 for p in x])
    ax.set_xticklabels(category_names, rotation=45, ha="right")
    ax.set_title("Issues by Category")
    ax.set_ylabel("# of Issues")
    ax.legend()

    # Save bar chart to BytesIO buffer
    bar_chart_buffer = BytesIO()
    plt.savefig(bar_chart_buffer, format="PNG", bbox_inches="tight")
    plt.close(fig)
    bar_chart_buffer.seek(0)

    # Embed bar chart in the PDF
    bar_chart_image = Image.open(bar_chart_buffer)
    pdf.drawInlineImage(bar_chart_image, (PAGE_WIDTH / 2) - 200, PAGE_HEIGHT - 500, width=400, height=200)

    # Add pie charts
    add_pie_charts(pdf, categories, open_issues_count, closed_issues_count)


def add_pie_charts(pdf, categories, open_issues_count, closed_issues_count):
    # --- Pie Chart 1: Categories Distribution ---
    labels1 = list(categories.keys())
    sizes1 = [sum(cat_data.values()) for cat_data in categories.values()]
    colors1 = plt.cm.tab20.colors[:len(labels1)]

    fig1, ax1 = plt.subplots()
    ax1.pie(
        sizes1,
        labels=labels1,
        autopct="%1.1f%%" if sum(sizes1) > 0 else None,
        startangle=90,
        colors=colors1,
    )
    ax1.set_title("Complaint Categories Distribution")

    # Save first pie chart to buffer
    pie1_buffer = BytesIO()
    plt.savefig(pie1_buffer, format="PNG", bbox_inches="tight")
    pie1_buffer.seek(0)
    plt.close(fig1)
    pie1_image = Image.open(pie1_buffer)

    # Embed first pie chart in the PDF
    pdf.drawInlineImage(pie1_image, MARGIN + 50, PAGE_HEIGHT - 730, width=200, height=200)

    # --- Pie Chart 2: Open vs Closed Issues ---
    labels2 = ["Open Issues", "Closed Issues"]
    sizes2 = [open_issues_count, closed_issues_count]
    colors2 = ["orange", "blue"]

    fig2, ax2 = plt.subplots()
    ax2.pie(
        sizes2,
        labels=labels2,
        autopct="%1.1f%%" if sum(sizes2) > 0 else None,
        startangle=90,
        colors=colors2,
    )
    ax2.set_title("Open vs Closed Issues")

    # Save second pie chart to buffer
    pie2_buffer = BytesIO()
    plt.savefig(pie2_buffer, format="PNG", bbox_inches="tight")
    pie2_buffer.seek(0)
    plt.close(fig2)
    pie2_image = Image.open(pie2_buffer)

    # Embed second pie chart in the PDF
    pdf.drawInlineImage(pie2_image, MARGIN + 250, PAGE_HEIGHT - 730, width=200, height=200)


def add_table(pdf, table_data, start_y, width=((PAGE_WIDTH - 2 * MARGIN) / 2) - PAGE_WIDTH/3.5):
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    table.wrapOn(pdf, width, PAGE_HEIGHT - start_y)
    table.drawOn(pdf, width, start_y)

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 30  # Margin around the page

def add_table_d(pdf, table_data, start_y, page_width=PAGE_WIDTH - 2 * MARGIN, page_height=PAGE_HEIGHT):
    # Define column widths dynamically
    col_widths = [page_width / len(table_data[0])] * len(table_data[0])

    # Style for wrapped text
    styles = getSampleStyleSheet()
    cell_style = styles['BodyText']
    cell_style.wordWrap = 'CJK'  # Enable word wrapping

    # Wrap text in cells using Paragraph
    wrapped_data = []
    for row in table_data:
        wrapped_row = [Paragraph(str(cell), cell_style) for cell in row]
        wrapped_data.append(wrapped_row)

    # Create the table
    table = Table(wrapped_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # Calculate available height for the table
    available_height = start_y - MARGIN
    table_height = table.wrap(page_width, available_height)[1]

    # Handle table overflow to the next page if needed
    if table_height > available_height:
        rows_per_page = int(available_height // 27)  # Approximate rows per page
        header = [wrapped_data[0]]  # Keep the header row separate
        data_rows = wrapped_data[1:]

        while data_rows:
            page_data = header + data_rows[:rows_per_page]
            table = Table(page_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            table.wrap(page_width, available_height)
            table.drawOn(pdf, MARGIN, start_y - table.wrap(page_width, available_height)[1])

            # Move to the next page if rows are remaining
            data_rows = data_rows[rows_per_page:]
            if data_rows:
                pdf.showPage()
                draw_border(pdf)  # Ensure border is redrawn
                start_y = page_height - MARGIN
    else:
        table.wrap(page_width, available_height)
        table.drawOn(pdf, MARGIN, start_y - table_height)


# Add footer with page number
def add_footer(pdf, page_no):
    pdf.setFont("Helvetica", 10)
    pdf.drawString(PAGE_WIDTH / 2 - 20, MARGIN / 2, f"Page {page_no}")

# Add blank page at the end
def add_blank_page(pdf):
    draw_border(pdf)
    # pdf.setFont("Helvetica-Italic", 14)
    pdf.drawString(PAGE_WIDTH / 2 - 100, PAGE_HEIGHT / 2, "This page is intentionally left blank.")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(PAGE_WIDTH / 2 - 35, MARGIN / 2, "End of Report")



async def generate_pdf_utility(from_date, to_date, issues, db):
    """
    Generate a PDF report with maintenance statistics.
    
    Args:
        from_date: Start date for the report
        to_date: End date for the report
        issues: List of issues/complaints
        db: Database connection
        
    Returns:
        Response object with the generated PDF
    """
    # Convert dates to string format for display
    from_date_str = from_date.strftime("%Y-%m-%d")
    to_date_str = to_date.strftime("%Y-%m-%d")
    
    # Initialize counters and accumulators
    total_days = 0
    closed_issues_count = 0
    open_issues_count = 0
    total_close_time = 0
    complaint_categories = {}

    for issue in issues:
        try:
            # Extract issue details
            status = issue.get("status")
            category = issue["issue"].get("issueCat", "Unknown")
            logs = issue.get("log", [])

            # Count open and closed issues
            if status == "CLOSE":
                closed_issues_count += 1
            elif status == "OPEN":
                open_issues_count += 1

            # Calculate the most common category
            complaint_categories[category] = complaint_categories.get(category, 0) + 1

            # Calculate total days from logs and closing times
            if logs:
                start_date = datetime.strptime(logs[0]["date"], "%d-%m-%y %H:%M")
                close_dates = [
                    datetime.strptime(log["date"], "%d-%m-%y %H:%M")
                    for log in logs
                    if log["action"] == "closed"
                ]
                if close_dates:
                    total_days += (close_dates[-1] - start_date).days
                    total_close_time += sum(
                        (close_date - start_date).days for close_date in close_dates
                    )

        except Exception as e:
            print(f"Error processing issue {issue.get('_id')}: {e}")

    # Compute metrics
    total_issues = closed_issues_count + open_issues_count
    avg_close_time = total_close_time / closed_issues_count if closed_issues_count > 0 else 0
    most_common_category = max(complaint_categories, key=complaint_categories.get) if complaint_categories else "N/A"

    # PDF generation remains unchanged, update table_data with new metrics
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    # Page 1: Overview
    draw_border(pdf)
    add_sigma_header(pdf)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(((PAGE_WIDTH - 2 * MARGIN) / 2) - 40, PAGE_HEIGHT - 150, "Maintenance Statistics Report")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(((PAGE_WIDTH - 2 * MARGIN) / 2) - 25, PAGE_HEIGHT - 170, f"From {from_date_str} to {to_date_str}")
    table_data = [
        ["Total # of Complaints", str(total_issues)],
        ["# of Closed Complaints", str(closed_issues_count)],
        ["# of Open Complaints", str(open_issues_count)],
        ["Average Time Taken to Close a Complaint", f"{avg_close_time:.2f} days"],
        ["Most Common Complaint Category", most_common_category],
    ]
    add_table(pdf, table_data, PAGE_HEIGHT - 280, ((PAGE_WIDTH - 2 * MARGIN) / 2) - PAGE_WIDTH / 8)
    add_charts(pdf, from_date, to_date,db)
    pdf.showPage()

    # Page 2: Detailed Table
    draw_border(pdf)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(PAGE_WIDTH / 2 - 100, PAGE_HEIGHT - 70, "Complaints in Given Time Range")
    pdf.setFont("Helvetica", 12)
    detailed_table_data = [
        ["Category", "Issue ID", "Raised By", "Date", "Location", "Days to Resolve"],
    ]
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    for issue in issues:
        detailed_table_data.append([
            issue["issue"].get("issueCat", "Unknown"),
            issue.get("issueNo", "N/A"),
            issue["raised_by"].get("name", "N/A"),
            issue.get("date", "N/A"),
            issue["issue"].get("block", "N/A"),
            str(total_days),  # Placeholder; you can make this specific to each issue
        ])  
#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


    add_table_d(pdf, detailed_table_data, start_y=PAGE_HEIGHT - 100)
    add_footer(pdf, 2)
    pdf.showPage()

    # Blank page at the end
    add_blank_page(pdf)

    # Save and return the PDF
    pdf.save()
    buffer.seek(0)

    return buffer   
