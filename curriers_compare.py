import pandas as pd
import streamlit as st

# הגדרת נתיבים קבועים
DHL_FILE_PATH = "dhl pricing 1.xlsx"  # עדכן לנתיב הנכון
FEDEX_FILE_PATH = "fedex pricing 1.xlsx"  # עדכן לנתיב הנכון

def calculate_dhl_price(pricing_df, weight, area):
    """מחשב מחיר DHL לפי משקל ואזור"""
    try:
        # מיפוי אזורים ל-Zone
        area_mapping = {
            1: "Zone AE", 2: "Zone BE", 3: "Zone CE", 
            4: "Zone DE", 5: "Zone EE", 6: "Zone FE",
            7: "Zone GE", 8: "Zone HE", 9: "Zone RE",
            10: "Zone TE", 11: "Zone VE"
        }
        
        zone_col = area_mapping.get(area)
        if not zone_col or zone_col not in pricing_df.columns:
            st.error(f"עמודה {zone_col} לא נמצאה עבור DHL")
            return 0
            
        # דילוג על השורה עם "Currency"
        numeric_df = pricing_df[pricing_df['KG'].apply(
            lambda x: isinstance(x, (int, float)) or 
                    (isinstance(x, str) and str(x).replace('.', '', 1).isdigit())
        )]
        
        # חיפוש המחיר לפי משקל
        weights = numeric_df['KG'].astype(float).tolist()
        closest_weight = min(weights, key=lambda x: abs(x - weight))
        row = numeric_df[numeric_df['KG'] == closest_weight]
        price = float(row[zone_col].values[0])
        
        return price
        
    except Exception as e:
        st.error(f"שגיאת DHL: {str(e)}")
        return 0

def calculate_fedex_price(pricing_df, weight, zone):
    """מחשב מחיר FedEx לפי משקל ואזור"""
    try:
        zone_col = zone  # נניח שה-zone כבר מכיל את שם העמודה המלא
        
        if zone_col not in pricing_df.columns:
            st.error(f"עמודה {zone_col} לא נמצאה עבור FedEx")
            return 0
            
        # דילוג על השורה עם "Currency"
        numeric_df = pricing_df[pricing_df['KG'].apply(
            lambda x: isinstance(x, (int, float)) or 
                    (isinstance(x, str) and str(x).replace('.', '', 1).isdigit())
        )]
        
        # חיפוש המחיר לפי משקל
        weights = numeric_df['KG'].astype(float).tolist()
        closest_weight = min(weights, key=lambda x: abs(x - weight))
        row = numeric_df[numeric_df['KG'] == closest_weight]
        price = float(row[zone_col].values[0])
        
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
        
        # מידע על מבנה הנתונים
        st.sidebar.subheader("מידע על הנתונים")
        st.sidebar.write(f"עמודות זמינות: {', '.join(dhl_pricing.columns.tolist())}")
        
        # ממשק משתמש
        country = st.selectbox("🇮🇱 בחר מדינה", sorted(dhl_mapping.iloc[:,0].unique()))
        weight = st.number_input("⚖️ משקל (ק״ג)", min_value=0.1, value=5.0, step=0.1)
        
        if st.button("השווה מחירים", type="primary"):
            # מציאת אזורים
            dhl_row = dhl_mapping[dhl_mapping.iloc[:,0] == country]
            fedex_row = fedex_mapping[fedex_mapping.iloc[:,0] == country.split(' (')[0]]
            
            if dhl_row.empty or fedex_row.empty:
                if dhl_row.empty:
                    st.error(f"לא נמצא מיפוי DHL עבור {country}")
                if fedex_row.empty:
                    st.error(f"לא נמצא מיפוי FedEx עבור {country.split(' (')[0]}")
                return
                
            dhl_area = dhl_row.iloc[0,1]
            fedex_zone = fedex_row.iloc[0,1]
            
            # הצגת אזורי מחיר
            st.info(f"DHL אזור: {dhl_area}, FedEx אזור: {fedex_zone}")
            
            # התאמת שמות אזורים לשמות העמודות בקובץ
            dhl_zone_name = f"Zone {chr(64+dhl_area)}E"  # ממיר מספר 1 ל-AE, 2 ל-BE וכו'
            fedex_zone_name = fedex_zone if "Zone" in fedex_zone else f"Zone {fedex_zone}"
            
            # חישוב מחירים
            dhl_price = calculate_dhl_price(dhl_pricing, weight, dhl_area)
            fedex_price = calculate_fedex_price(fedex_pricing, weight, fedex_zone_name)
            
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
                st.success(f"✅ {cheaper} חסכון של ${price_diff:.2f} ({savings:.1f}%)")
            elif dhl_price > 0:
                st.success("✅ רק DHL מציע שירות למדינה זו במחיר ${dhl_price:.2f}")
            elif fedex_price > 0:
                st.success("✅ רק FedEx מציע שירות למדינה זו במחיר ${fedex_price:.2f}")
            else:
                st.warning("⚠️ לא נמצאו מחירים תקפים לשתי החברות")
                
    except Exception as e:
        st.error(f"🚨 שגיאה כללית: {str(e)}")

if __name__ == "__main__":
    main()
