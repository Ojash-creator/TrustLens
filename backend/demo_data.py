from __future__ import annotations
import hashlib
from typing import Any

def _did(title):
    return "0x3bcb" + hashlib.md5(title.encode()).hexdigest()[:8] + ":0x" + hashlib.md5(title[::-1].encode()).hexdigest()[:10]

def place(title, rating, reviews, address, website=None, phone=None, type_=None):
    p = {"title": title, "data_id": _did(title), "rating": rating, "reviews": reviews, "type": type_, "address": address}
    if website: p["website"] = website
    if phone: p["phone"] = phone
    return p

def maps(*places):
    return {"search_information": {"local_results_state": "Results for exact spelling"}, "local_results": list(places)}

def web(*rows):
    return {"organic_results": [{"position": i + 1, "title": t, "link": l, "snippet": s} for i, (t, l, s) in enumerate(rows)]}

def news(*rows):
    return {"news_results": [{"position": i + 1, "title": t, "source": {"name": src}, "date": d, "link": l, "snippet": s}
                             for i, (t, src, d, l, s) in enumerate(rows)]}

def jobs(*rows):
    return {"jobs_results": [{"title": t, "company_name": c, "location": loc, "via": f"via {via}",
                              "detected_extensions": {"posted_at": posted}, "apply_options": [{"title": via, "link": link}]}
                             for (t, c, loc, via, posted, link) in rows]}

def shopping(*rows):
    return {"shopping_results": [{"position": i + 1, "title": t, "source": seller, "price": f"\u20b9{p:,}",
                                  "extracted_price": p, "product_link": l} for i, (seller, t, p, l) in enumerate(rows)]}

def reviews(*rows):
    return {"reviews": [{"user": {"name": u}, "rating": r, "date": d, "snippet": txt} for (r, txt, d, u) in rows]}

HEADPHONES = "Sony WH-1000XM5 Wireless Noise Cancelling Headphones"
MARKET = [
    ("GadgetHub India", HEADPHONES, 24990, "https://gadgethub.example/xm5"),
    ("SoundStreet", HEADPHONES + " (Black)", 25490, "https://soundstreet.example/xm5"),
    ("KartBazaar", HEADPHONES, 26999, "https://kartbazaar.example/xm5"),
    ("ElectroMart", HEADPHONES + " (Silver)", 22990, "https://electromart.example/xm5"),
    ("AudioVilla", HEADPHONES, 27490, "https://audiovilla.example/xm5"),
    ("TechNest", HEADPHONES + " (Midnight Blue)", 24499, "https://technest.example/xm5"),
    ("PlayNow Electronics", HEADPHONES, 29990, "https://playnow.example/xm5"),
    ("Bazaar24", HEADPHONES + " (Black)", 21990, "https://bazaar24.example/xm5"),
]

SAMPLES: list[dict[str, Any]] = [
    {"id": "job-fake-wfh", "mode": "job", "expected": "high_risk",
     "title": "The work-from-home offer that asks for a fee",
     "blurb": "A WhatsApp message promises \u20b94,000 a day for typing. There is a catch.",
     "inputs": {"name": "SwiftHire Global Services", "role": "Data Entry Executive (Work From Home)", "location": "Hyderabad",
                "email": "hr.swifthire.global@gmail.com",
                "message": ("Congratulations! You are selected for Data Entry Executive (Work From Home) at SwiftHire Global Services. "
                            "No interview required, direct joining. Earn \u20b94,000 daily by simple typing tasks. To confirm your seat, "
                            "pay a refundable registration fee of \u20b92,499 and send your Aadhaar and bank details on WhatsApp only. "
                            "Only 5 vacancies left, hurry!")},
     "responses": {
        "google_maps:maps": maps(place("Swift Print Solutions", 4.1, 38, "Shop 12, Abids Road, Hyderabad, Telangana 500001",
                                       None, "+91 40 5550 1234", "Printing service")),
        "google_jobs:jobs": jobs(
            ("Data Entry Operator", "Meridian BPO Services", "Hyderabad, Telangana", "LinkedIn", "3 days ago", "https://jobs.example/meridian-1"),
            ("Data Entry Executive", "Orbit Staffing", "Hyderabad, Telangana", "Naukri", "1 week ago", "https://jobs.example/orbit-2")),
        "google:web": web(
            ("SwiftHire Global Services: scam or genuine?", "https://www.consumer-complaints-board.in/swifthire-global-services",
             "Several candidates report paying a registration fee for a data entry job at SwiftHire Global Services. Beware of this fake offer."),
            ("Beware: SwiftHire Global Services work-from-home offer is a fraud", "https://forum.jobseekers-india.in/t/swifthire-wfh",
             "Got a WhatsApp message from SwiftHire Global Services promising \u20b94,000 per day. Classic fraud, do not pay."),
            ("How to spot fake work-from-home jobs", "https://www.cybersafe-india.in/fake-wfh-jobs",
             "Job scammers use names such as SwiftHire Global Services and ask for refundable deposits."),
            ("Data Entry Jobs in Hyderabad", "https://www.freshjobs-hyd.in/data-entry",
             "Swift Hire Global Services hiring 50 candidates, work from home, no experience needed."),
            ("Work from home typing jobs: can you really earn \u20b94000 daily?", "https://www.wfhtips.in/typing-jobs",
             "Read the fine print before paying any fee for online work.")),
        "google:followup": web(
            ("r/jobscams: SwiftHire Global Services registration fee experience", "https://www.reddit.com/r/jobscams/comments/swifthire",
             "Paid \u20b92,499 to SwiftHire Global Services and the number is now switched off. Fraud."),
            ("Consumer complaint: SwiftHire Global Services refund not received", "https://www.complaints-forum.in/swifthire",
             "Candidate paid the registration fee to SwiftHire Global Services on request. Refund not received after 30 days.")),
        "google_news:news": news(
            ("Cyber police warn of fake work-from-home jobs asking for registration fees", "City Herald", "2 weeks ago",
             "https://cityherald.example/cyber-wfh-warning", "Police say fraudsters are using names like SwiftHire Global Services.")),
     }},
    {"id": "job-legit-analyst", "mode": "job", "expected": "trustworthy",
     "title": "An interview invite from a real analytics company",
     "blurb": "A final-round invite that checks out on every count.",
     "inputs": {"name": "Kestrel Analytics Pvt Ltd", "role": "Junior Data Analyst", "location": "Hyderabad",
                "email": "careers@kestrelanalytics.in",
                "message": ("Hi Priya, thank you for interviewing for the Junior Data Analyst role. We would like to schedule the final round "
                            "on Friday at our Madhapur office. Please bring your original ID for verification on the day. "
                            "No fee is charged at any stage of hiring.")},
     "responses": {
        "google_maps:maps": maps(place("Kestrel Analytics Pvt Ltd", 4.4, 312, "Plot 41, HITEC City Road, Madhapur, Hyderabad, Telangana 500081",
                                       "https://www.kestrelanalytics.in/", "+91 40 5550 0123", "Software company")),
        "google_jobs:jobs": jobs(
            ("Junior Data Analyst", "Kestrel Analytics", "Hyderabad, Telangana", "LinkedIn", "5 days ago", "https://jobs.example/kestrel-1"),
            ("Junior Data Analyst", "Kestrel Analytics Pvt Ltd", "Hyderabad, Telangana", "Kestrel Careers", "2 days ago", "https://kestrelanalytics.example/careers/jda"),
            ("Data Analyst (Fresher)", "Meridian Insights", "Hyderabad, Telangana", "Naukri", "1 week ago", "https://jobs.example/meridian-3")),
        "google:web": web(
            ("Careers at Kestrel Analytics | Join our Hyderabad team", "https://www.kestrelanalytics.in/careers",
             "Kestrel Analytics is hiring analysts, engineers and designers. Applications are free at every stage of hiring."),
            ("Kestrel Analytics reviews: work culture, salaries and interview questions", "https://www.workplace-reviews.in/kestrel-analytics",
             "Employees rate Kestrel Analytics 4.2 for work-life balance. Interview process: two technical rounds and one HR round."),
            ("Is Kestrel Analytics legit? Company profile", "https://www.companycheck.in/kestrel-analytics-pvt-ltd",
             "Kestrel Analytics Pvt Ltd is a registered private limited company in Telangana. No scam reports found."),
            ("Kestrel Analytics | LinkedIn", "https://www.linkedin.com/company/kestrel-analytics",
             "Kestrel Analytics, analytics and data engineering company headquartered in Hyderabad."),
            ("Kestrel Analytics opens second delivery centre", "https://www.deccanbusinessdaily.example/kestrel-centre",
             "The company plans to add 300 roles across analytics and engineering.")),
        "google_news:news": news(
            ("Kestrel Analytics opens second Hyderabad centre, plans to hire 300", "Deccan Business Daily", "1 month ago",
             "https://deccanbusinessdaily.example/kestrel-centre", "Kestrel Analytics expanded its Madhapur presence."),
            ("Kestrel Analytics raises Series B funding to expand its analytics platform", "StartupBrief India", "3 months ago",
             "https://startupbrief.example/kestrel-series-b", "The funding will support product and hiring.")),
     }},
    {"id": "job-bpo-mixed", "mode": "job", "expected": "caution",
     "title": "A real company, but the details are shaky",
     "blurb": "A call-centre role with staffing-agency postings and salary complaints.",
     "inputs": {"name": "Bluepeak Outsourcing", "role": "Customer Support Associate", "location": "Hyderabad",
                "email": "recruitment@bluepeakoutsourcing.in",
                "message": "Salary \u20b922,000 per month plus incentives. 2 weeks paid training. Joining in 3 days, please confirm on WhatsApp."},
     "responses": {
        "google_maps:maps": maps(place("Bluepeak Outsourcing", 3.5, 27, "2nd Floor, Kavuri Hills, Madhapur, Hyderabad, Telangana 500033",
                                       "http://bluepeakoutsourcing.in", "+91 40 5550 7788", "Call centre")),
        "google_maps_reviews:reviews": reviews(
            (2, "Salary was delayed twice and HR gave no response when I asked. Team leads are fine though.", "3 months ago", "Ravi K."),
            (3, "Targets are tough, but the team is friendly and training was okay.", "5 months ago", "Anita S."),
            (3, "Incentives are paid late. Work timings keep changing.", "7 months ago", "Imran P.")),
        "google_jobs:jobs": jobs(
            ("Customer Support Associate (client: Bluepeak)", "TalentBridge Staffing", "Hyderabad, Telangana", "LinkedIn", "1 week ago", "https://jobs.example/talentbridge-9")),
        "google:web": web(
            ("Bluepeak Outsourcing reviews: salary delay and deduction problems", "https://www.workplace-reviews.in/bluepeak-outsourcing",
             "Some employees mention delayed salary and deducted training charges at Bluepeak Outsourcing, while others praise the support team."),
            ("Bluepeak Outsourcing: company profile", "https://www.companycheck.in/bluepeak-outsourcing",
             "Bluepeak Outsourcing operates customer support and back-office services from Hyderabad."),
            ("Bluepeak Outsourcing careers", "http://bluepeakoutsourcing.in/careers",
             "Join the Bluepeak Outsourcing support team. Openings for customer support associates."),
            ("Anyone facing delayed salary at Bluepeak Outsourcing?", "https://forum.jobseekers-india.in/t/bluepeak-salary",
             "Delayed salary for two months and no response from HR. Refund of the deducted training amount is still pending.")),
     }},
    {"id": "job-unknown", "mode": "job", "expected": "insufficient",
     "title": "A tiny firm with almost no online trace",
     "blurb": "No red flags, but not much evidence either. TrustLens says so instead of guessing.",
     "inputs": {"name": "Nimbus Ventures LLP", "role": "Office Assistant", "location": "Warangal", "email": "hr@nimbusventures.in", "message": ""},
     "responses": {
        "google_maps:maps": maps(place("Nimbus Tutorials", 4.6, 14, "Hanamkonda, Warangal, Telangana 506001", None, None, "Tutoring service")),
        "google_jobs:jobs": {"jobs_results": []},
        "google:web": web(("Warangal jobs today: office assistant openings", "https://www.localjobs-tg.in/warangal",
                           "Latest office assistant jobs in Warangal with salary details.")),
     }},
    {"id": "shop-fake-headphones", "mode": "shop", "expected": "high_risk",
     "title": "Premium headphones at 80% off",
     "blurb": "An Instagram ad, a brand-new .top website and a price nobody else can match.",
     "inputs": {"name": "MegaDealz Outlet", "url": "https://megadealz-official-outlet.top/product/sony-wh-1000xm5",
                "product": "Sony WH-1000XM5 wireless headphones", "price": "4999",
                "message": ("FLASH SALE TODAY ONLY! 85% OFF. Only 3 pieces left. No COD, pay 100% advance to our personal UPI number "
                            "and send screenshot on WhatsApp. No returns.")},
     "responses": {
        "google_shopping:shopping": shopping(*MARKET),
        "google_maps:maps": {"local_results": []},
        "google:web": web(
            ("MegaDealz Outlet reviews: fake shop? Customers report not receiving orders", "https://www.consumer-complaints-board.in/megadealz-outlet",
             "Customers say MegaDealz Outlet took payment for headphones and never delivered. Fake website, avoid."),
            ("megadealz-official-outlet.top scam alert", "https://www.scamcheck-india.in/megadealz-official-outlet-top",
             "This site was created recently and copies product photos from real stores. MegaDealz Outlet shows several scam indicators."),
            ("How to spot fake online stores selling branded electronics at 80% off", "https://www.cybersafe-india.in/fake-online-stores",
             "Sites like megadealz-official-outlet.top ask for full advance payment on personal UPI IDs and never ship the product.")),
        "google:followup": web(
            ("r/scams_india: MegaDealz Outlet headphones never arrived", "https://www.reddit.com/r/scams_india/comments/megadealz",
             "Ordered from MegaDealz Outlet after an Instagram ad, paid by UPI, no delivery, no reply. Fraud.")),
        "google_news:news": {"news_results": []},
     }},
    {"id": "shop-legit-headphones", "mode": "shop", "expected": "trustworthy",
     "title": "The same headphones from an established store",
     "blurb": "A fair price, a known seller and a clean website.",
     "inputs": {"name": "UrbanCart India", "url": "https://www.urbancart.in/p/sony-wh-1000xm5",
                "product": "Sony WH-1000XM5 wireless headphones", "price": "24990", "message": ""},
     "responses": {
        "google_shopping:shopping": shopping(("UrbanCart India", HEADPHONES, 24990, "https://www.urbancart.in/p/sony-wh-1000xm5"), *MARKET[:7]),
        "google_maps:maps": maps(place("UrbanCart India", 4.3, 1208, "Kondapur, Hyderabad, Telangana 500084",
                                       "https://www.urbancart.in", "+91 40 5550 9090", "Electronics store")),
        "google:web": web(
            ("UrbanCart India: official store", "https://www.urbancart.in/", "Shop laptops, audio and phones from UrbanCart India with 7-day easy returns."),
            ("UrbanCart India reviews and customer ratings", "https://www.reviewhub.in/urbancart-india",
             "Buyers praise fast delivery and easy returns at UrbanCart India."),
            ("UrbanCart India return policy", "https://www.urbancart.in/returns", "Return most items within 7 days of delivery."),
            ("Is UrbanCart India safe? Store check", "https://www.companycheck.in/urbancart-india",
             "UrbanCart India has traded since 2016 and is GST registered. No scam reports found.")),
        "google_news:news": {"news_results": []},
     }},
    {"id": "local-coaching-advance", "mode": "local", "expected": "high_risk",
     "title": "A coaching institute wants the full fee upfront",
     "blurb": "Guaranteed selection, 100% advance, no refund. Reviews tell the rest.",
     "inputs": {"name": "BrightPath IAS Academy", "location": "New Delhi",
                "message": "They want 100% advance payment of \u20b985,000, promise guaranteed selection, and say no refund under any condition."},
     "responses": {
        "google_maps:maps": maps(place("BrightPath IAS Academy", 2.6, 48, "Old Rajinder Nagar, New Delhi, Delhi 110060",
                                       "http://brightpathias.in", "+91 11 5550 3344", "Coaching centre")),
        "google_maps_reviews:reviews": reviews(
            (1, "Paid the full fee in advance because they promised guaranteed selection. Classes were cancelled and they refuse to refund. Total fraud.", "2 months ago", "Aditya M."),
            (1, "Teachers changed every month. Asked for a refund within a week and got abused on the phone. Waste of money.", "4 months ago", "Neha R."),
            (2, "Fake promises about results. The brochure batch never started.", "5 months ago", "Sandeep T."),
            (1, "They cheated many students with the advance fee scheme. Please stay away.", "6 months ago", "Kavya J."),
            (2, "Study material was poor and nobody answers calls after admission.", "8 months ago", "Rohit B.")),
        "google:web": web(
            ("BrightPath IAS Academy fraud? Students allege fee not refunded", "https://www.consumer-complaints-board.in/brightpath-ias-academy",
             "Aspirants allege BrightPath IAS Academy collected full advance fees, promised guaranteed selection and refused refunds. Several call it a scam."),
            ("Beware of BrightPath IAS Academy advance fee offer", "https://forum.upsc-aspirants.in/t/brightpath-advance-fee",
             "Do not pay the advance. BrightPath IAS Academy cheated multiple students in the last batch."),
            ("BrightPath IAS Academy: courses and fees", "http://brightpathias.in/courses", "Foundation and prelims batches at BrightPath IAS Academy.")),
        "google:followup": web(
            ("r/UPSC: BrightPath IAS Academy refund experience", "https://www.reddit.com/r/UPSC/comments/brightpath",
             "Paid \u20b985,000 to BrightPath IAS Academy. Guaranteed selection was a lie and they will not refund. Fraud.")),
        "google_news:news": news(
            ("Consumer commission directs coaching institute to refund \u20b985,000 to aspirant", "Capital Times", "3 weeks ago",
             "https://capitaltimes.example/coaching-refund", "The order concerns BrightPath IAS Academy, which had promised guaranteed selection."),
            ("BrightPath IAS Academy faces student protest over refund", "Metro Post", "2 months ago", "https://metropost.example/brightpath-protest",
             "Students of BrightPath IAS Academy gathered outside the centre demanding refunds.")),
     }},
    {"id": "local-dental-clinic", "mode": "local", "expected": "trustworthy",
     "title": "A neighbourhood dental clinic",
     "blurb": "Hundreds of reviews, full contact details and only ordinary complaints.",
     "inputs": {"name": "Green Leaf Dental Clinic", "location": "Bengaluru", "message": ""},
     "responses": {
        "google_maps:maps": maps(place("Green Leaf Dental Clinic", 4.8, 642, "12th Main, Indiranagar, Bengaluru, Karnataka 560038",
                                       "https://www.greenleafdental.in", "+91 80 5550 2211", "Dental clinic")),
        "google_maps_reviews:reviews": reviews(
            (3, "Had to wait 40 minutes past my appointment time, but the treatment itself was good.", "1 month ago", "Meera V."),
            (3, "Parking is difficult nearby. The doctor was gentle and explained everything.", "3 months ago", "Arjun N."),
            (4, "Front desk took a while to confirm my slot.", "4 months ago", "Sheela D.")),
        "google:web": web(
            ("Green Leaf Dental Clinic, Indiranagar", "https://www.greenleafdental.in/", "Family dentistry, braces and implants in Indiranagar, Bengaluru."),
            ("Green Leaf Dental Clinic reviews and appointments", "https://www.clinic-directory.in/green-leaf-dental", "Patients rate Green Leaf Dental Clinic highly for hygiene and clear pricing."),
            ("Green Leaf Dental Clinic: doctors and treatments", "https://www.healthbook.in/green-leaf-dental-clinic", "Book a check-up at Green Leaf Dental Clinic. Fees are listed upfront.")),
        "google_news:news": {"news_results": []},
     }},
]

SAMPLE_INDEX = {s["id"]: s for s in SAMPLES}

def public_samples():
    return [{k: v for k, v in s.items() if k != "responses"} for s in SAMPLES]
