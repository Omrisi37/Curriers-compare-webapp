import pandas as pd
import streamlit as st

# הגדרת נתיבים קבועים לקבצים
DHL_FILE_PATH = "dhl pricing 1.xlsx"  # עדכן את הנתיב לקובץ DHL שלך
FEDEX_FILE_PATH = "fedex pricing 1.xlsx"  # עדכן את הנתיב לקובץ FedEx שלך

def calculate_dhl_price(pricing_df, weight, area):
    """
    מחשב את מחיר המשלוח ב-DHL לפי משקל ואזור
    """
    try:
        # טבלת מחירים בסיסית
        basic_pricing = pricing_df[pricing_df['KG'].apply(
            lambda x: isinstance(x, (int, float)) or 
                    (isinstance(x, str) and str(x).replace('.', '', 1).isdigit())
        )]
        
        # חיפוש שורות תוספת מחיר
        extra_10kg_row = None
        extra_30kg_row = None
        
        for i, row in pricing_df.iterrows():
            if isinstance(row['KG'], str):
                if "extra" in str(row['KG']).lower() and "10kg" in str(row['KG']).lower():
                    # חיפוש שורת המחירים לתוספת מעל 10 ק"ג
                    for j in range(i+1, min(i+5, len(pricing_df))):
                        if not pd.isna(pricing_df.iloc[j]['area1']):
                            extra_10kg_row = pricing_df.iloc[j]
                            break
                elif "extra" in str(row['KG']).lower() and "30" in str(row['KG']).lower():
                    # חיפוש שורת המחירים לתוספת מעל 30 ק"ג
                    for j in range(i+1, min(i+5, len(pricing_df))):
                        if not pd.isna(pricing_df.iloc[j]['area1']):
                            extra_30kg_row = pricing_df.iloc[j]
                            break
        
        # שם העמודה לפי האזור
        area_col = f"area{area}"
        
        # חישוב המחיר לפי טווח המשקל
        if weight <= 10:
            # מחיר ישיר מהטבלה הבסיסית
            weights = [float(w) for w in basic_pricing['KG'].tolist()]
            closest_weight = min(weights, key=lambda x: abs(float(x) - weight))
            row = basic_pricing[basic_pricing['KG'] == closest_weight]
            price = float(row[area_col].values[0])
            
        elif weight <= 30:
            # מחיר ל-10 ק"ג + תוספת לכל 0.5 ק"ג נוסף
            weights = [float(w) for w in basic_pricing['KG'].tolist()]
            closest_base = max([w for w in weights if w <= 10])
            base_row = basic_pricing[basic_pricing['KG'] == closest_base]
            base_price = float(base_row[area_col].values[0])
            
            extra_units = (weight - closest_base) / 0.5
            extra_price_per_unit = float(extra_10kg_row[area_col])
            
            price = base_price + (extra_units * extra_price_per_unit)
            
        else:  # weight > 30
            # חישוב מחיר בסיסי עד 30 ק"ג
            weights = [float(w) for w in basic_pricing['KG'].tolist()]
            closest_base = max([w for w in weights if w <= 10])
            base_row = basic_pricing[basic_pricing['KG'] == closest_base]
            base_price = float(base_row[area_col].values[0])
            
            # תוספת מחיר מ-10 עד 30 ק"ג
            extra_10_30_units = (30 - closest_base) / 0.5
            extra_10_30_price = float(extra_10kg_row[area_col]) * extra_10_30_units
            
            # תוספת מחיר מעל 30 ק"ג
            extra_30_plus_units = weight - 30
            extra_30_plus_price = float(extra_30kg_row[area_col]) * extra_30_plus_units
            
            price = base_price + extra_10_30_price + extra_30_plus_price
        
        return price
        
    except Exception as e:
        st.error(f"שגיאה בחישוב מחיר DHL: {e}")
        return 0

def calculate_fedex_price(pricing_df, weight, zone):
    """
    מחשב את מחיר המשלוח ב-FedEx לפי משקל ואזור
    """
    try:
        zone_col = f"Zone {zone}"
        
        # חיפוש בטבלה הבסיסית (עד 24 ק"ג)
        if weight <= 24:
            basic_rows = pricing_df[pricing_df['KG'].apply(
                lambda x: isinstance(x, (int, float)) or 
                        (isinstance(x, str) and str(x).replace('.', '', 1).isdigit())
            )]
            
            # מציאת המשקל הקרוב ביותר
            weights = [float(w) for w in basic_rows['KG'].tolist() if pd.notna(w)]
            closest_weight = min(weights, key=lambda x: abs(float(x) - weight))
            row = basic_rows[basic_rows['KG'] == closest_weight]
            price = float(row[zone_col].values[0])
            
        else:  # weight > 24
            # חיפוש בשאר הטבלה - IP או IPF
            
            # מציאת חלק ה-IP בטבלה
            ip_start = None
            ipf_start = None
            
            for i, row in pricing_df.iterrows():
                if isinstance(row.iloc[0], str) and 'IP - International Priority' in row.iloc[0]:
                    ip_start = i + 2  # +2 כדי לדלג על כותרות
                elif isinstance(row.iloc[0], str) and 'IPF - International Priority Freight' in row.iloc[0]:
                    ipf_start = i + 2  # +2 כדי לדלג על כותרות
            
            # בדיקה ב-IP (משקל 31-150 ק"ג)
            if ip_start and weight >= 31:
                ip_end = ipf_start - 2 if ipf_start else len(pricing_df)
                
                for i in range(ip_start, ip_end):
                    kg_range = pricing_df.iloc[i]['KG']
                    if isinstance(kg_range, str):
                        if '-' in kg_range:
                            low, high = map(int, kg_range.split('-'))
                            if low <= weight <= high:
                                return float(pricing_df.iloc[i][zone_col]) * weight
                        elif '+' in kg_range:
                            low = int(kg_range.replace('+', ''))
                            if weight >= low:
                                return float(pricing_df.iloc[i][zone_col]) * weight
            
            # בדיקה ב-IPF (משקל 68+ ק"ג)
            if ipf_start and weight >= 68:
                for i in range(ipf_start, len(pricing_df)):
                    if i >= len(pricing_df) or pd.isna(pricing_df.iloc[i]['KG']):
                        continue
                        
                    kg_range = pricing_df.iloc[i]['KG']
                    if isinstance(kg_range, str):
                        if '-' in kg_range:
                            low, high = map(int, kg_range.split('-'))
                            if low <= weight <= high:
                                return float(pricing_df.iloc[i][zone_col]) * weight
                        elif '+' in kg_range:
                            low = int(kg_range.replace('+', ''))
                            if weight >= low:
                                return float(pricing_df.iloc[i][zone_col]) * weight
            
            # אם לא נמצא תעריף מתאים, השתמש בהערכה
            st.warning(f"לא נמצא תעריף מדויק למשקל {weight}kg, משתמש בהערכה")
            
            # ניקח את התעריף האחרון הזמין
            if weight < 68:
                # שימוש ב-IP
                max_ip_row = pricing_df.iloc[ip_start + 4]  # 150+ שורה
                price = float(max_ip_row[zone_col]) * weight
            else:
                # שימוש ב-IPF
                max_ipf_row = pricing_df.iloc[ipf_start + 5]  # 1000+ שורה
                price = float(max_ipf_row[zone_col]) * weight
        
        return price
    
    except Exception as e:
        st.error(f"שגיאה בחישוב מחיר FedEx: {e}")
        return 0

def main():
    st.title("מחשבון השוואת מחירי משלוחים")
    
    try:
        # טעינת קבצים
        st.sidebar.info(f"טוען נתונים מ: {DHL_FILE_PATH}")
        st.sidebar.info(f"טוען נתונים מ: {FEDEX_FILE_PATH}")
        
        # טעינת גיליונות מחירים ומיפוי
        dhl_pricing = pd.read_excel(DHL_FILE_PATH, sheet_name="pricing per area per kg")
        dhl_mapping = pd.read_excel(DHL_FILE_PATH, sheet_name="areas codes")
        
        fedex_pricing = pd.read_excel(FEDEX_FILE_PATH, sheet_name="pricing per area per kg")
        fedex_mapping = pd.read_excel(FEDEX_FILE_PATH, sheet_name="areas codes")
        
        st.sidebar.success("כל הקבצים נטענו בהצלחה")
        
        # רשימת מדינות להשוואה
        countries = sorted(dhl_mapping.iloc[:, 0].unique())
        
        # ממשק משתמש
        selected_country = st.selectbox("בחר מדינה", countries)
        weight = st.number_input("משקל המשלוח (ק\"ג)", min_value=0.1, value=5.0, step=0.1)
        
        if st.button("השווה מחירים"):
            # מציאת האזור המתאים לכל חברה
            dhl_row = dhl_mapping[dhl_mapping.iloc[:, 0] == selected_country]
            
            # הסרת קוד המדינה אם קיים
            country_name = selected_country
            if "(" in selected_country and ")" in selected_country:
                country_name = selected_country.split(" (")[0].strip()
            
            fedex_row = fedex_mapping[fedex_mapping.iloc[:, 0] == country_name]
            
            if not dhl_row.empty and not fedex_row.empty:
                # קבלת אזורי המחיר
                dhl_area = int(dhl_row.iloc[0, 1])
                fedex_zone = fedex_row.iloc[0, 1]
                
                # חישוב מחירים
                dhl_price = calculate_dhl_price(dhl_pricing, weight, dhl_area)
                fedex_price = calculate_fedex_price(fedex_pricing, weight, fedex_zone)
                
                # הצגת תוצאות
                st.subheader("תוצאות ההשוואה")
                
                comparison_data = {
                    "חברת שילוח": ["DHL", "FedEx"],
                    "אזור": [f"אזור {dhl_area}", f"אזור {fedex_zone}"],
                    "מחיר ($)": [f"${dhl_price:.2f}", f"${fedex_price:.2f}"]
                }
                
                comparison_df = pd.DataFrame(comparison_data)
                st.dataframe(comparison_df)
                
                # הצגת החברה הזולה יותר
                if dhl_price < fedex_price:
                    cheaper = "DHL"
                    price_diff = fedex_price - dhl_price
                    savings_percent = (price_diff / fedex_price) * 100
                else:
                    cheaper = "FedEx"
                    price_diff = dhl_price - fedex_price
                    savings_percent = (price_diff / dhl_price) * 100
                
                st.success(f"**{cheaper}** זולה יותר ב-**${price_diff:.2f}** ({savings_percent:.1f}%)")
            else:
                if dhl_row.empty:
                    st.error(f"לא נמצא מיפוי עבור המדינה: {selected_country} בטבלת DHL")
                if fedex_row.empty:
                    st.error(f"לא נמצא מיפוי עבור המדינה: {country_name} בטבלת FedEx")
    
    except Exception as e:
        st.error(f"אירעה שגיאה: {e}")

if __name__ == "__main__":
    main()
