import pandas as pd
import streamlit as st

# הגדרת נתיבים קבועים לקבצים
DHL_FILE_PATH = "dhl pricing 1.xlsx"  # עדכן לנתיב הנכון
FEDEX_FILE_PATH = "fedex pricing 1.xlsx"  # עדכן לנתיב הנכון

def calculate_dhl_price(pricing_df, weight, area):
    """מחשב מחיר DHL לפי משקל ואזור"""
    try:
        # המרת מספר האזור לשם העמודה בטבלה
        area_mapping = {
            1: "Zone AE", 2: "Zone BE", 3: "Zone CE", 
            4: "Zone DE", 5: "Zone EE", 6: "Zone FE",
            7: "Zone GE", 8: "Zone HE", 9: "Zone RE",
            10: "Zone TE", 11: "Zone VE"
        }
        
        zone_col = area_mapping.get(int(area))
        if not zone_col or zone_col not in pricing_df.columns:
            st.error(f"שגיאת DHL: עמודה {zone_col} לא נמצאה")
            return 0
        
        # סינון השורות עם ערכים מספריים בלבד
        numeric_rows = []
        for i, row in pricing_df.iterrows():
            try:
                # נסיון להמיר את ערך ה-KG למספר
                float(row['KG'])
                numeric_rows.append(i)
            except (ValueError, TypeError):
                # דילוג על שורות כמו "Currency"
                continue
        
        filtered_df = pricing_df.iloc[numeric_rows]
        
        # מציאת המשקל הקרוב ביותר
        weights = [float(w) for w in filtered_df['KG']]
        closest_weight = min(weights, key=lambda x: abs(x - weight))
        
        # חישוב המחיר
        price_row = filtered_df[filtered_df['KG'] == closest_weight]
        price = float(price_row[zone_col].values[0])
        
        return price
        
    except Exception as e:
        st.error(f"שגיאת DHL: {str(e)}")
        return 0

def calculate_fedex_price(pricing_df, weight, zone):
    """מחשב מחיר FedEx לפי משקל ואזור"""
    try:
        # ודא שהאזור כולל את התחילית "Zone"
        zone_col = zone if "Zone" in zone else f"Zone {zone}"
        
        if zone_col not in pricing_df.columns:
            st.error(f"שגיאת FedEx: עמודה {zone_col} לא נמצאה")
            return 0
        
        # סינון השורות עם ערכים מספריים בלבד
        numeric_rows = []
        for i, row in pricing_df.iterrows():
            try:
                # נסיון להמיר את ערך ה-KG למספר
                float(row['KG'])
                numeric_rows.append(i)
            except (ValueError, TypeError):
                # דילוג על שורות כמו "Currency"
                continue
        
        filtered_df = pricing_df.iloc[numeric_rows]
        
        # מציאת המשקל הקרוב ביותר
        weights = [float(w) for w in filtered_df['KG']]
        closest_weight = min(weights, key=lambda x: abs(x - weight))
        
        # חישוב המחיר
        price_row = filtered_df[filtered_df['KG'] == closest_weight]
        price = float(price_row[zone_col].values[0])
        
        return price
    
    except Exception as e:
        st.error(f"שגיאת FedEx: {str(e)}")
        return 0

def main():
    st.title("🛩️ השוואת מחירי משלוחים")
    
    try:
        # טעינת נתונים
        dhl_pricing = pd.read_excel(DHL_FILE_PATH, sheet_name="pricing per area per kg")
        dhl_mapping = pd.read_excel(DHL_FILE_PATH, sheet_name="areas codes")
        
        fedex_pricing = pd.read_excel(FEDEX_FILE_PATH, sheet_name="pricing per area per kg") 
        fedex_mapping = pd.read_excel(FEDEX_FILE_PATH, sheet_name="areas codes")
        
        # ממשק משתמש
        country = st.selectbox("🇮🇱 בחר מדינה", sorted(dhl_mapping.iloc[:,0].unique()))
        weight = st.number_input("⚖️ משקל (ק״ג)", min_value=0.1, value=5.0, step=0.1)
        
        if st.button("השווה מחירים", type="primary"):
            # מציאת האזורים לפי המדינה
            dhl_row = dhl_mapping[dhl_mapping.iloc[:,0] == country]
            
            # טיפול במדינות עם קוד בסוגריים
            country_name = country
            if "(" in country and ")" in country:
                country_name = country.split(" (")[0].strip()
            
            fedex_row = fedex_mapping[fedex_mapping.iloc[:,0] == country_name]
            
            if dhl_row.empty:
                st.error(f"לא נמצא מיפוי DHL למדינה: {country}")
                return
                
            if fedex_row.empty:
                st.error(f"לא נמצא מיפוי FedEx למדינה: {country_name}")
                return
            
            # קבלת אזורי המחיר
            dhl_area = dhl_row.iloc[0,1]
            fedex_zone = fedex_row.iloc[0,1]
            
            # חישוב מחירים
            dhl_price = calculate_dhl_price(dhl_pricing, weight, dhl_area)
            fedex_price = calculate_fedex_price(fedex_pricing, weight, fedex_zone)
            
            # הצגת תוצאות
            st.subheader("📊 תוצאות השוואה")
            results = {
                "חברה": ["DHL", "FedEx"],
                "מחיר ($)": [dhl_price, fedex_price]
            }
            st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)
            
            # חישוב חסכון
            if dhl_price > 0 and fedex_price > 0:
                cheaper = "DHL" if dhl_price < fedex_price else "FedEx"
                price_diff = abs(dhl_price - fedex_price)
                max_price = max(dhl_price, fedex_price)
                savings = (price_diff / max_price) * 100
                st.success(f"✅ {cheaper} זולה יותר ב-${price_diff:.2f} ({savings:.1f}%)")
            elif dhl_price > 0:
                st.success(f"✅ רק DHL מציע שירות למדינה זו במחיר ${dhl_price:.2f}")
            elif fedex_price > 0:
                st.success(f"✅ רק FedEx מציע שירות למדינה זו במחיר ${fedex_price:.2f}")
            else:
                st.warning("⚠️ לא נמצאו מחירים תקפים לשתי החברות")
                
    except Exception as e:
        st.error(f"🚨 שגיאה כללית: {str(e)}")

if __name__ == "__main__":
    main()
