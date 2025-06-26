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
    st.title("Admin Login")

    email = st.text_input("Admin Username")
    password = st.text_input("Admin password", type="password")
    if st.button("Login"):

            try:
                res = requests.post(f"{BACKEND_URL}/token/",json={"username": email, "password": password})
                if res.status_code == 200:
                    token = res.json()
                    access_token = token.get("access")
                    st.session_state["admin_token"]= access_token
                    print(st.session_state.get("admin_token"))
                    st.session_state["is_admin"] = True
                    st.session_state["admin_auth_pending"] = False
                    st.success("Admin Authenticated")
                    st.rerun()
                else:
                    st.error(f"Unauthorized - {res.status_code}")
            except Exception as e:
                st.error(f"Login failed - {e}")


            


def fetch_admin_results(page):
    headers = {"Authorization":f"Bearer {st.session_state.get('admin_token')}"}
    try:
        res = requests.get(f"{BACKEND_URL}/admin-results/?page={page}", headers=headers)
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

    if st.sidebar.button("Log Out"):
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
                "department": st.session_state.get("department_id"),
                "total_credits":total_credits,
                "total_grade_points": total_points
            })

            if response.status_code == 201:
                st.info("Your GPA has been saved")
            else:
                st.error("Your GPA not saved")
        else:
            st.warning("No valid grades to calculate CGPA.")

def main():
    
    st.sidebar.markdown("## Admin Panel")

    if "admin_auth_pending" not in st.session_state:
        st.session_state["admin_auth_pending"] = False

    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False

    if st.sidebar.button("Show All Logs (Admin Only)"):
        st.session_state["admin_auth_pending"] = True
        st.session_state["is_admin"] = False
        st.rerun()

    if st.session_state["admin_auth_pending"] and not st.session_state["is_admin"]:
        admin_authenticate() 
        st.stop()

    if st.session_state["is_admin"]:
        admin_dashboard()
        st.stop()

    
    
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

                if st.button("Calculate Overall CGPA"):
                    email = st.session_state.get("user_email")
                    dept_id = st.session_state.get("department_id")
                    try:
                        res = requests.get(f"{BACKEND_URL}/calculate-cgpa/", params={"email": email,"dept_id":dept_id})

                        if res.status_code == 200:
                            data = res.json()
                            cgpa = data.get("cgpa")
                            semester_count = data.get("semester_count")
                            st.success(f"Your Overall CGPA is: **{cgpa}** (calculated from {semester_count} semesters)")
                        else:
                            st.warning(res.json().get("error", "Could not fetch CGPA"))
                    except Exception as e:
                        st.error(f"Error occurred: {e}")
                
                
                delete_target = st.session_state.pop("delete_target", None)
                if delete_target:
                    # st.write("Deleting record for:", delete_target) 
                    # print("Deleting record for:", delete_target) 
                    try:
                        delete_res = requests.delete(
                            f"{BACKEND_URL}/delete-result/",
                            params=delete_target
                        )
                        if delete_res.status_code == 200:
                            st.success(f"Deleted Semester {delete_target['semester']} result.")
                        else:
                            st.error("Failed to delete result.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error occurred: {e}")
                        st.rerun()

    
                if st.button("View & Manage Logs"):
                    st.session_state["view_logs"] = True
                    st.session_state["delete_target"] = None
                    st.rerun()

                if st.session_state.get("view_logs"):
                    email = st.session_state.get("user_email")
                    dept_id = st.session_state.get("department_id")

                    res = requests.get(f"{BACKEND_URL}/user-history/", params={
                        "email": email,
                        "dept_id": dept_id
                    })

                    if res.status_code == 200:
                        history = res.json().get("history", [])
                        if history:
                            st.markdown("### Your CGPA History (with Delete Option):")
                            for item in history:
                                if str(item["department"]) == str(dept_id):
                                    col1, col2 = st.columns([4, 1])
                                    with col1:
                                        st.markdown(
                                            f"Semester {item['semester']} → **CGPA: {item['cgpa']}** → at {item['created_at']}"
                                        )
                                    with col2:
                                        delete_key = f"delete_{item['semester']}"
                                        if st.button("❌", key=delete_key):
                                            st.session_state["delete_target"] = {
                                                "email": email,
                                                "semester": item["semester"],
                                                "department": dept_id
                                            }
                                            st.rerun()
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
