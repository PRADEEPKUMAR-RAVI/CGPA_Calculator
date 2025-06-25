import streamlit as st
import requests
import re

BACKEND_URL = "http://localhost:8000/api"

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def send_otp(email):
    res = requests.post(f"{BACKEND_URL}/send-otp/", json={"email": email})
    return res.json()

def verify_otp(email, otp):
    res = requests.post(f"{BACKEND_URL}/verify-otp/", json={"email": email, "otp": otp})
    return res.json()

GRADE_POINT_MAP = {
    "O": 10,
    "A+": 9,
    "A": 8,
    "B+": 7,
    "B": 6,
    "C": 5,
}

def fetch_subjects(semester, department_code):
    res = requests.get(f"{BACKEND_URL}/subjects/{semester}/{department_code}/")
    if res.status_code == 200:
        return res.json().get("subjects", [])
    return []

def fetch_semesters():
    res = requests.get(f"{BACKEND_URL}/semesters/")
    if res.status_code == 200:
        return res.json().get("semesters", [])
    return []

def admin_authenticate():
    st.title("Admin Authentication")

    email = st.text_input("Admin Email")
    password = st.text_input("Admin password", type="password")

    if email and is_valid_email(email=email):
        if email == "admin@gmail.com" and password == "admin1234":
            st.session_state["is_admin"] = True
            st.session_state.pop("admin_auth_pending", None)
            st.rerun()

        else:
            st.error("Invalid Credentials")
    else:
        st.error("Invalid email")


def fetch_admin_results(page):
    try:
        res = requests.get(f"{BACKEND_URL}/admin-results/?page={page}")
        if res.status_code == 200:
            data = res.json()
            count = data.get("count", 0)
            page_size = 5  
            total_pages = (count + page_size - 1) // page_size  
            return {
                "results": data.get("results", []),
                "next": data.get("next"),
                "previous": data.get("previous"),
                "total_pages": total_pages
            }
    except Exception as e:
        st.error(f"Failed to fetch admin results: {e}")
    return {"results": [], "next": None, "previous": None, "total_pages": 1}



def admin_dashboard():
    st.title("All CGPA Logs - Admin View")

    page = st.session_state.get("admin_page", 1)
    data = fetch_admin_results(page)

    results = data.get("results", [])
    total_pages = data.get("total_pages", 1)
    next_page = data.get("next")
    prev_page = data.get("previous")

    if not results:
        st.info("No results available.")
        return

    for r in results:
        st.markdown(f"""
        **Email**: {r['email']}  
        **CGPA**: {r['cgpa']}  
        **Semester**: {r['semester']}  
        **Department**: {r.get('department', 'N/A')}  
        **Date**: {r['created_at']}
        --------------------------
        """)

    if st.button("Exit"):
        st.session_state["admin_auth_pending"] = False
        st.session_state["is_admin"] = False
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if prev_page and st.button("<-- Previous"):
            st.session_state["admin_page"] = page - 1
            st.rerun()

    with col2:
        if next_page and st.button("Next -->"):
            st.session_state["admin_page"] = page + 1
            st.rerun()

   
    st.markdown(f"Page {page} of {total_pages}")






def subject_grade_input(semester, department_code):
    subjects = fetch_subjects(semester, department_code)
    total_credits = 0
    total_points = 0

    st.markdown(f"### Semester {semester}")

    for subject in subjects:
        code = subject["code"]
        name = subject["name"]
        credit = subject["credit"]

        st.markdown(f"#### {code} - {name}")

        status = st.selectbox(
            f"Status for {code}",
            options=["PASS", "ARREAR"],
            key=f"{code}_status"
        )

        grade = None
        if status == "PASS":
            grade = st.radio(
                f"Grade for {code}",
                options=["O", "A+", "A", "B+", "B", "C"],
                horizontal=True,
                key=f"{code}_grade"
            )

        if status == "PASS" and grade:
            gp = GRADE_POINT_MAP.get(grade, 0)
            total_credits += credit
            total_points += gp * credit

    if st.button("Calculate CGPA"):
        if total_credits > 0:
            cgpa = total_points / total_credits
            st.success(f"🎓 Your CGPA for Semester {semester} is **{round(cgpa, 2)}**")

            response = requests.post(f"{BACKEND_URL}/save-result/", json={
                "email": st.session_state.get("user_email"),
                "cgpa": round(cgpa, 2),
                "semester": semester,
                "department": st.session_state.get("department_id")
            })

            if response.status_code == 201:
                st.info("Your GPA has been saved")
            else:
                st.error("Your GPA not saved")
        else:
            st.warning("No valid grades to calculate CGPA.")

def main():

    st.title("CGPA Calculator 🎓")

    
    try:
        response = requests.get(f"{BACKEND_URL}/departments/")
        response.raise_for_status()
        departments = response.json().get("departments", [])
    except Exception as e:
        st.error(f"Error fetching departments: {e}")
        st.stop()

    dept_names = [d["name"] for d in departments]
    selected_dept = st.selectbox("Select Department", ["Select"] + dept_names)

    if selected_dept != "Select":
        
        selected_dept_obj = next((d for d in departments if d["name"] == selected_dept), None)
        if selected_dept_obj:
            st.session_state["department_code"] = selected_dept_obj["code"]
            st.session_state["department_id"] = selected_dept_obj["id"]
            print("Dep_code --------------------", selected_dept_obj["code"])

        email = st.text_input("Enter your email to continue:")

        if email and is_valid_email(email):
            if st.button("Send OTP"):
                resp = send_otp(email)
                if "message" in resp:
                    st.success("OTP sent to your email.")

            otp_input = st.text_input("Enter the OTP sent to your email")

            if st.button("Verify OTP"):
                verify_result = verify_otp(email, otp_input)
                if verify_result.get("verified"):
                    st.success("Email verified")
                    st.session_state["user_email"] = email
                    st.session_state["email_verified"] = True
                else:
                    st.error("OTP verification failed. " + verify_result.get("error", ""))

            if st.session_state.get("email_verified") and st.session_state.get("department_code"):
                if st.button("Show All Logs (Admin Only)"):
                    st.session_state["admin_auth_pending"] = True
                    st.rerun()

                if st.session_state.get("admin_auth_pending"):
                    admin_authenticate()
                    return
                if st.session_state.get("is_admin"):
                    admin_dashboard()
                    return

                if st.button("View Logs"):
                    email = st.session_state.get("user_email")
                    res = requests.get(f"{BACKEND_URL}/user-history/", params={"email": email})
                    if res.status_code == 200:
                        history = res.json().get("history", [])
                        if history:
                            st.markdown("### Your CGPA History:")
                            for item in history:
                                st.markdown(f"- Semester {item['semester']} → **CGPA: {item['cgpa']}** → **Dept_Code:{item['department']}** → at {item['created_at']}")
                        else:
                            st.info("No history found.")
                    else:
                        st.error("Failed to fetch history.")

                semesters = fetch_semesters()
                semester = st.selectbox("Select your Semester", semesters)
                if semester:
                    subject_grade_input(semester, st.session_state["department_code"])
                    
        elif email:
            st.error("Invalid email format")

if __name__ == '__main__':
    main()
