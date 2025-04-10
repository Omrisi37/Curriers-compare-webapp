import pandas as pd
import streamlit as st

# הגדרת נתיבים קבועים לקבצים
DHL_FILE_PATH = "dhl pricing 1.xlsx"  # הגדר כאן את הנתיב הקבוע לקובץ DHL
FEDEX_FILE_PATH = "fedex pricing 1.xlsx"  # הגדר כאן את הנתיב הקבוע לקובץ FedEx

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
        
        # מציאת שורות תוספת מחיר
        extra_10kg_row = None
        extra_30kg_row = None
        
        for i, row in pricing_df.iterrows():
            if isinstance(row['KG'], str):
                if "extra0.5 kg above 10kg" in row['KG']:
                    extra_10kg_row = pricing_df.iloc[i+2]  # שורה מתחת לכותרת
                elif "extra 1kg30.1-99,999" in row['KG']:
                    extra_30kg_row = pricing_df.iloc[i+2]  # שורה מתחת לכותרת
        
        # שם העמודה לפי האזור
        area_col = f"area{area}"
        
        # חישוב המחיר לפי טווח המשקל
        if weight <= 10:
            # מחיר ישיר מהטבלה הבסיסית
            weights = basic_pricing['KG'].astype(float).tolist()
            closest_weight = min(weights, key=lambda x: abs(float(x) - weight))
            row = basic_pricing[basic_pricing['KG'] == closest_weight]
            price = float(row[area_col].values[0])
            
        elif weight <= 30:
            # מחיר ל-10 ק"ג + תוספת לכל 0.5 ק"ג נוסף
            weights = basic_pricing['KG'].astype(float).tolist()
            base_weight = max([w for w in weights if w <= 10])
            base_row = basic_pricing[basic_pricing['KG'] == base_weight]
            base_price = float(base_row[area_col].values[0])
            
            extra_units = (weight - base_weight) / 0.5
            extra_price_per_unit = float(extra_10kg_row[area_col])
            
            price = base_price + (extra_units * extra_price_per_unit)
            
        else:  # weight > 30
            # חישוב מחיר עד 30 ק"ג ואז תוספת לכל 1 ק"ג נוסף
            weights = basic_pricing['KG'].astype(float).tolist()
            
            # מחיר בסיסי ל-10 ק"ג
            base_weight = max([w for w in weights if w <= 10])
            base_row = basic_pricing[basic_pricing['KG'] == base_weight]
            base_price = float(base_row[area_col].values[0])
            
            # תוספת מ-10 עד 30 ק"ג
            extra_10_30_units = (30 - base_weight) / 0.5
            extra_10_30_price = extra_10kg_row[area_col] * extra_10_30_units
            
            # תוספת מעל 30 ק"ג
            extra_30_plus_units = weight - 30
            extra_30_plus_price = extra_30kg_row[area_col] * extra_30_plus_units
            
            price = base_price + extra_10_30_price + extra_30_plus_price
        
        return price
        
    except Exception as e:
        st.error(f"שגיאה בחישוב מחיר DHL: {e}")
        return 0

def calculate_fedex_price(pricing_df, ip_df, ipf_df, weight, zone):
    """
    מחשב את מחיר המשלוח ב-FedEx לפי משקל ואזור
    """
    try:
        # שם העמודה לפי האזור
        zone_col = f"Zone {zone}"
        
        if weight <= 24:
            # טבלת מחירים בסיסית
            weights = pricing_df['KG'].astype(float).tolist()
            closest_weight = min(weights, key=lambda x: abs(float(x) - weight))
            row = pricing_df[pricing_df['KG'] == closest_weight]
            price = float(row[zone_col].values[0])
            
        elif weight <= 150:  # בדיקה בטבלת IP
            # מציאת הטווח המתאים בטבלת IP
            for i, row in ip_df.iterrows():
                try:
                    kg_range = row['KG']
                    if "-" in kg_range:
                        low, high = map(int, kg_range.split("-"))
                        if low <= weight <= high:
                            price_per_kg = float(row[zone_col])
                            return price_per_kg * weight
                    elif "+" in kg_range:
                        low = int(kg_range.replace("+", ""))
                        if weight >= low:
                            price_per_kg = float(row[zone_col])
                            return price_per_kg * weight
                except:
                    continue
            
        else:  # בדיקה בטבלת IPF למשלוחים כבדים
            # מציאת הטווח המתאים בטבלת IPF
            for i, row in ipf_df.iterrows():
                try:
                    kg_range = row['KG']
                    if "-" in kg_range:
                        low, high = map(int, kg_range.split("-"))
                        if low <= weight <= high:
                            price_per_kg = float(row[zone_col])
                            return price_per_kg * weight
                    elif "+" in kg_range:
                        low = int(kg_range.replace("+", ""))
                        if weight >= low:
                            price_per_kg = float(row[zone_col])
                            return price_per_kg * weight
                except:
                    continue
            
        return price
    
    except Exception as e:
        st.error(f"שגיאה בחישוב מחיר FedEx: {e}")
        return 0

def main():
    st.title("מחשבון השוואת מחירי משלוחים")
    
    try:
        # טעינת קבצי מחירים קבועים
        st.sidebar.info(f"טוען נתונים מ: {DHL_FILE_PATH}")
        st.sidebar.info(f"טוען נתונים מ: {FEDEX_FILE_PATH}")
        
        # טעינת קבצי DHL
        dhl_pricing = pd.read_excel(DHL_FILE_PATH, sheet_name=0)  # טבלת מחירים
        dhl_mapping = pd.read_excel(DHL_FILE_PATH, sheet_name=1)  # מיפוי מדינות
        
        # טעינת קבצי FedEx
        fedex_pricing = pd.read_excel(FEDEX_FILE_PATH, sheet_name=0)  # טבלת מחירים בסיסית
        fedex_ip = pd.read_excel(FEDEX_FILE_PATH, sheet_name=1)  # טבלת IP
        fedex_ipf = pd.read_excel(FEDEX_FILE_PATH, sheet_name=2)  # טבלת IPF
        fedex_mapping = pd.read_excel(FEDEX_FILE_PATH, sheet_name=3)  # מיפוי מדינות
        
        st.sidebar.success("כל הקבצים נטענו בהצלחה")
        
        # רשימת מדינות
        countries = sorted(dhl_mapping.iloc[:, 0].unique())
        
        # ממשק משתמש - בחירת מדינה ומשקל
        selected_country = st.selectbox("בחר מדינה", countries)
        weight = st.number_input("משקל המשלוח (ק\"ג)", min_value=0.1, value=5.0, step=0.1)
        
        if st.button("השווה מחירים"):
            # מציאת האזור לכל חברה
            dhl_row = dhl_mapping[dhl_mapping.iloc[:, 0] == selected_country]
            
            # הסרת קוד המדינה אם יש צורך
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
                fedex_price = calculate_fedex_price(fedex_pricing, fedex_ip, fedex_ipf, weight, fedex_zone)
                
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
                
                # פירוט החישוב
                with st.expander("פירוט החישוב"):
                    st.write(f"**DHL (אזור {dhl_area}):**")
                    if weight <= 10:
                        st.write(f"מחיר ישיר לפי משקל {weight}kg: ${dhl_price:.2f}")
                    elif weight <= 30:
                        st.write(f"מחיר בסיסי (10kg) + תוספת לכל 0.5kg נוסף = ${dhl_price:.2f}")
                    else:
                        st.write(f"מחיר בסיסי (30kg) + תוספת לכל 1kg נוסף = ${dhl_price:.2f}")
                    
                    st.write(f"**FedEx (אזור {fedex_zone}):**")
                    if weight <= 24:
                        st.write(f"מחיר ישיר לפי משקל {weight}kg: ${fedex_price:.2f}")
                    elif weight <= 150:
                        st.write(f"חישוב לפי IP: {weight}kg × מחיר לק\"ג = ${fedex_price:.2f}")
                    else:
                        st.write(f"חישוב לפי IPF: {weight}kg × מחיר לק\"ג = ${fedex_price:.2f}")
            else:
                if dhl_row.empty:
                    st.error(f"לא נמצא מיפוי עבור המדינה: {selected_country} בטבלת DHL")
                if fedex_row.empty:
                    st.error(f"לא נמצא מיפוי עבור המדינה: {country_name} בטבלת FedEx")
    
    except Exception as e:
        st.error(f"אירעה שגיאה: {e}")

if __name__ == "__main__":
    main()
