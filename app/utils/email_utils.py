import os
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Optional, Union


from app.config import settings

def render_template(template_name, **kwargs):
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    return template.render(**kwargs)

def url_for(endpoint: str, **values):
    # A simple implementation for the static endpoint
    if endpoint == "static":
        filename = values.get("filename", "")
        return f"/static/{filename}"
    # Extend for other endpoints if necessary
    return ""

def sendmail(
    mail_met: Dict[str, str],
    receiver: str,
    subject: str,
    short_subject: str,
    text: str,
    html: Optional[str] = "NOT INPUT BY USER."
) -> None:
    mailid = settings.EMAILID
    mailps = settings.EMAILPS
    if html == "NOT INPUT BY USER.":
        html = render_template(
            "email.html",
            mail=receiver,
            message=text,
            subject=short_subject,
            mail_met=mail_met,
        )

    sender_email = mailid
    receiver_email = receiver
    password = mailps
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())



def notify_hod_or_club(
    issue_data: Dict[str, Union[str, list]], 
    hod_email: Optional[str] = None, 
    club_email: Optional[str] = None
) -> None:
    # Check if either HoD email or club advisor email is provided
    if not hod_email and not club_email:
        #print("No HoD or Club Advisor email available. No email sent.")
        return

    # Generate the email body with issue details
    issue_details = f"""
    Dear Sir/Madam,  
    <br/>A student under your department or club has raised the following issue:  
    <br/><br/>
    <table style="border-collapse: collapse; width: 100%; text-align: left;">
        <tr>
            <th style="border: 1px solid black; padding: 8px;">Detail</th>
            <th style="border: 1px solid black; padding: 8px;">Description</th>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;"><b>Student Name</b></td>
            <td style="border: 1px solid black; padding: 8px;">{issue_data['name']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;"><b>Student ID</b></td>
            <td style="border: 1px solid black; padding: 8px;">{issue_data['id']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;"><b>Issue Type</b></td>
            <td style="border: 1px solid black; padding: 8px;">{issue_data['issueType']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;"><b>Issue Category</b></td>
            <td style="border: 1px solid black; padding: 8px;">{issue_data['issueCat']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;"><b>Issue Content</b></td>
            <td style="border: 1px solid black; padding: 8px;">{issue_data['issueContent']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;"><b>Block</b></td>
            <td style="border: 1px solid black; padding: 8px;">{issue_data['block']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;"><b>Floor</b></td>
            <td style="border: 1px solid black; padding: 8px;">{issue_data['floor']}</td>
        </tr>
        <tr>
            <td style="border: 1px solid black; padding: 8px;"><b>Action Item</b></td>
    <br/><br/>Thank you for your attention.  
    """

    # Define email subject and short subject
    subject = "[PSG-GMS-SIGMA] Student Issue Notification"
    short_subject = "Student Issue Notification"

    # Determine recipients dynamically
    recipients = []
    if hod_email:
        recipients.append(hod_email)
    if club_email:
        recipients.append(club_email)

    # Loop through recipients and send emails
    for receiver_email in recipients:
        sendmail(
            mail_met={"type": "student_issue_notification"},
            receiver=receiver_email,
            subject=subject,
            short_subject=short_subject,
            text=issue_details,
        )

    #print(f"Email sent to: {', '.join(recipients)}")


def department_hod(department):
    map = {
        "Apparel & Fashion Design": "22n228@psgtech.ac.in", # hod.afd@psgtech
        "Applied Mathematics & Computational Sciences": "hod.amcs@psgtech",
        "Applied Science": "hod.apsc@psgtech",
        "Automobile Engineering": "snk.auto@psgtech",
        "Biotechnology": "mas.bio@psgtech",
        "Biomedical Engineering": "rvp.bme@psgtech",
        "Chemistry": "ctr.chem@psgtech",
        "Civil Engineering": "hod.civil@psgtech",
        "Computer Science & Engineering": "hod.cse@psgtech",
        "Electronics & Communication Engineering": "vk.ece@psgtech",
        "Electrical & Electronics Engineering": "jkr.eee@psgtech",
        "English": "hod.english@psgtech",
        "Fashion Technology": "kcs.fashion@psgtech",
        "Humanities": "hod.hum@psgtech",
        "Instrumentation & Control Systems Engineering": "jas.ice@psgtech",
        "Information Technology": "hod.it@psgtech",
        "Mathematics": "cpg.maths@psgtech",
        "Computer Applications": "ac.mca@psgtech",
        "Mechanical Engineering": "prt.mech@psgtech",
        "Metallurgical Engineering": "jkm.metal@psgtech",
        "Physics": "ksk.phy@psgtech",
        "Production Engineering": "msk.prod@psgtech",
        "Robotics & Automation Engineering": "hod.rae@psgtech",
        "Textile Technology": "hod.textile@psgtech"
    }
    return  map.get(department, None)



