import pandas as pd
import streamlit as st

# הגדרת נתיבים קבועים לקבצים
DHL_FILE_PATH = "dhl pricing 2.xlsx"  # עדכן לנתיב הנכון
FEDEX_FILE_PATH = "fedex pricing 2.xlsx"  # עדכן לנתיב הנכון

def calculate_price(pricing_df, weight, area):
    """
    מחשב מחיר לפי משקל ואזור - פונקציה משותפת ל-DHL ו-FedEx
    """
    try:
        area_col = f"area_{area}"
        
        if area_col not in pricing_df.columns:
            st.error(f"עמודה {area_col} לא נמצאה בטבלת המחירים")
            return 0
        
        # מציאת המשקל הקרוב ביותר בטבלה
        weights = pricing_df["Weight (kg)"].tolist()
        closest_weight = min(weights, key=lambda x: abs(float(x) - weight))
        
        # קבלת המחיר המתאים
        price = float(pricing_df[pricing_df["Weight (kg)"] == closest_weight][area_col].values[0])
        
        return price
        
    except Exception as e:
        st.error(f"שגיאה בחישוב המחיר: {str(e)}")
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
        
        debug_mode = st.sidebar.checkbox("הצג מידע טכני")
        if debug_mode:
            st.sidebar.write("עמודות DHL:", dhl_pricing.columns.tolist())
            st.sidebar.write("עמודות FedEx:", fedex_pricing.columns.tolist())
        
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
            fedex_area = fedex_row.iloc[0,1]
            
            if debug_mode:
                st.sidebar.write(f"DHL אזור: {dhl_area}, FedEx אזור: {fedex_area}")
            
            # חישוב מחירים
            dhl_price = calculate_price(dhl_pricing, weight, dhl_area)
            fedex_price = calculate_price(fedex_pricing, weight, fedex_area)
            
            # הצגת תוצאות
            st.subheader("📊 תוצאות השוואה")
            results = {
                "חברה": ["DHL", "FedEx"],
                "מחיר ($)": [f"${dhl_price:.2f}", f"${fedex_price:.2f}"]
            }
            
            st.dataframe(pd.DataFrame(results), hide_index=True, use_container_width=True)
            
            # חישוב חסכון
            if dhl_price > 0 and fedex_price > 0:
                if dhl_price < fedex_price:
                    cheaper = "DHL"
                    price_diff = fedex_price - dhl_price
                    max_price = fedex_price
                else:
                    cheaper = "FedEx"
                    price_diff = dhl_price - fedex_price
                    max_price = dhl_price
                
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
