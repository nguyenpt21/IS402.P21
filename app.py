import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta, date
import os
from dotenv import load_dotenv

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")


st.write("""
## Dự đoán khoản vay có trả được 
""")

st.subheader("Nhập thủ công")

naics_mapping = {
    '11': 'Ag/For/Fish/Hunt',
    '21': 'Min/Quar/Oil_Gas_ext',
    '22': 'Utilities',
    '23': 'Construction',
    '31': 'Manufacturing',
    '32': 'Manufacturing',
    '33': 'Manufacturing',
    '42': 'Wholesale_trade',
    '44': 'Retail_trade',
    '45': 'Retail_trade',
    '48': 'Trans/Ware',
    '49': 'Trans/Ware',
    '51': 'Information',
    '52': 'Finance/Insurance',
    '53': 'RE/Rental/Lease',
    '54': 'Prof/Science/Tech',
    '55': 'Mgmt_comp',
    '56': 'Admin_sup/Waste_Mgmt_Rem',
    '61': 'Educational',
    '62': 'Healthcare/Social_assist',
    '71': 'Arts/Entertain/Rec',
    '72': 'Accom/Food_serv',
    '81': 'Other_no_pub',
    '92': 'Public_Admin'
}

state_mapping = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
}

left_col, right_col = st.columns(2)

with left_col:
    state = st.selectbox("Bang",state_mapping.values(), placeholder="Bang")
    noemp = st.number_input("Số lượng nhân viên của doanh nghiệp", min_value=0, step=1)
    create_job = st.number_input("Số lượng công việc được tạo mới", min_value=0, step=1)
    franchise_code = st.text_input("Mã nhượng quyền")
    rev_line_cr = st.selectbox("Sử dụng tín dụng luân chuyển", ['Có', 'Không'])
    disbursemen_date = st.date_input("Ngày giải ngân")
    gr_appv = st.number_input("Tổng số tiền vay được phê duyệt", step=1)

with right_col:
    naics = st.text_input("NAICS")
    term = st.number_input("Kỳ hạn khoản vay (tháng)", min_value=0, step=1)
    retained_job = st.number_input("Số lượng công việc được duy trì", min_value=0, step=1)
    urban_rural = st.selectbox("Vùng", ["Thành thị", "Nông thôn"])
    lowdoc = st.selectbox("Sử dụng chương trình cho vay Lowdoc", ['Có', 'Không'])
    new_business = st.selectbox("Doanh nghiệp mới", ['Có', 'Không'])
    sba_appv = st.number_input("Số tiền bảo lãnh của SBA", step=1)

if st.button("Dự đoán"):
    is_franchised = 0 if int(franchise_code) <=1 else 1
    industry_code = naics[:2]
    industry_name = naics_mapping.get(industry_code, "Other_no_pub")
    active =disbursemen_date + timedelta(days=term*30)
    recession = 1 if active > date(2007,12, 1) and active < date(2009, 6, 30) else 0

    data = {
        'Term': term,
        'NoEmp': noemp,
        'CreateJob': create_job,
        'RetainedJob': retained_job,
        'UrbanRural': 1 if urban_rural == "Thành thị" else 0,
        'RevLineCr': 1 if rev_line_cr == "Có" else 0,
        'LowDoc': 1 if lowdoc == "Có" else 0,
        'NewBusiness': 1 if new_business == "Có" else 0,
        'IsFranchised': is_franchised,
        'Industry_Name': industry_name,
        'Recession': recession,
        'RealEstate': 1 if term >= 240 else 0,
        'Portion': sba_appv / gr_appv,
        'State_Name': state,
        'SBA_Appv': sba_appv,
        'GrAppv': gr_appv
    }

    headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }

    try:
        response = requests.post(
                AZURE_ENDPOINT,
                headers=headers,
                json={"Inputs": {"input1": [data]}}

            )
        result = response.json()

        if "Results" in result:
            predictions = result["Results"]["WebServiceOutput0"]

            df_predictions = pd.DataFrame(predictions)

            st.success("Dự đoán hoàn tất!")
            st.dataframe(df_predictions)
        else:
            st.error(f"Lỗi trả về từ Azure ML: {result}")

    except Exception as e:
        st.error(f"Lỗi khi gửi dữ liệu: {e}")



def process_csv_input(df):
    df['NewBusiness'] = df['NewExist'].apply(lambda x: 0 if x == 1 else 1)
    df['IsFranchised'] = df['FranchiseCode'].apply(lambda x: 0 if x <= 1 else 1)
    df['RevLineCr'] = df['RevLineCr'].apply(lambda x: 0 if x in ['N', '0'] else (1 if x in ['Y', '1'] else None))
    df['LowDoc'] = df['LowDoc'].apply(lambda x: 0 if x in ['N', '0'] else (1 if x in ['Y', '1'] else None))
    currency_columns = ['DisbursementGross', 'SBA_Appv', 'GrAppv']
    for col_name in currency_columns:
        df[col_name] = df[col_name].str.replace(r'[$,]', '', regex=True).astype(float)

    df['Industry'] = df['NAICS'].astype(str).str[:2]
    df['Industry_Name'] = df['Industry'].map(naics_mapping)
    df['DisbursementDate'] = df['DisbursementDate'].apply(
        lambda x: '0' + x if len(x) == 8 else x
    )

    def convert_date(date_str):
        if len(date_str) != 9:
            return pd.NaT
        
        day_month = date_str[:7]
        year_part = date_str[7:]
        year = '19' + year_part if int(year_part) > 25 else '20' + year_part
        try:
            return datetime.strptime(f"{day_month}{year}", "%d-%b-%Y")
        except:
            return pd.NaT

    df['DisbursementDate'] = df['DisbursementDate'].apply(convert_date)

    df['Active'] = df.apply(
        lambda row: row['DisbursementDate'] + timedelta(days=row['Term'] * 30) 
        if pd.notnull(row['DisbursementDate']) else pd.NaT,
        axis=1
    )

    recession_start = datetime(2007, 12, 1)
    recession_end = datetime(2009, 6, 30)
    df['Recession'] = df['Active'].apply(
        lambda x: 1 if (pd.notnull(x) and recession_start <= x <= recession_end) else 0
    )

    df['RealEstate'] = df['Term'].apply(lambda x: 1 if x >= 240 else 0)

    df['Portion'] = df['SBA_Appv'] / df['GrAppv']

    df['State_Name'] = df['State'].map(state_mapping)

    float_cols = [ "SBA_Appv", "GrAppv"]  # các cột cần giữ là float
    df[float_cols] = df[float_cols].astype(float)

    return df[['Term','NoEmp','CreateJob','RetainedJob',
               'UrbanRural','RevLineCr','LowDoc','GrAppv','SBA_Appv','NewBusiness',
               'IsFranchised','Industry_Name','State_Name','Recession','RealEstate','Portion']]

st.subheader("Tải file csv")

uploaded_file = st.file_uploader("Chọn file CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    st.write("Xem trước dữ liệu")
    st.dataframe(df.head())


    if st.button("Dự đoán"):
        df_show = df.copy()
        df_input = process_csv_input(df)
        records = df.to_dict(orient="records")
        st.write(records)

        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                AZURE_ENDPOINT,
                headers=headers,
                json={"Inputs": {"input1": records}}
            )
            result = response.json()

            if "Results" in result:
                outputs = result["Results"]["WebServiceOutput0"]

                predictions = []
                for output in outputs:
                    predictions.append(output['Scored Labels'])
                df_show['prediction'] = predictions

                st.success("✅ Dự đoán hoàn tất!")
                st.dataframe(df_show)

                # Cho phép tải file kết quả về
                csv = df_show.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Tải file kết quả", csv, "predicted_results.csv", "text/csv")
            else:
                st.error(f"❌ Lỗi trả về từ Azure ML: {result}")

        except Exception as e:
            st.error(f"❌ Lỗi khi gửi dữ liệu: {e}")