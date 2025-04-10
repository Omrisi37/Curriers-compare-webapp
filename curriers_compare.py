import pandas as pd
import streamlit as st

# הגדרת נתיבים קבועים
DHL_FILE_PATH = "dhl pricing 1.xlsx"  # עדכן לנתיב הנכון
FEDEX_FILE_PATH = "fedex pricing 1.xlsx"  # עדכן לנתיב הנכון

def calculate_dhl_price(pricing_df, weight, area):
    """מחשב מחיר DHL לפי משקל ואזור"""
    try:
        # טבלת מחירים בסיסית
        basic_pricing = pricing_df[pricing_df['KG'].apply(
            lambda x: isinstance(x, (int, float)) or 
                     (isinstance(x, str) and x.replace('.', '', 1).isdigit())
        )]
        
        # חיפוש תוספות מחיר
        extra_10kg_row = None
        extra_30kg_row = None
        
        for i, row in pricing_df.iterrows():
            if isinstance(row['KG'], str):
                if "extra0.5 kg above 10kg" in row['KG']:
                    extra_10kg_row = pricing_df.iloc[i+2]
                elif "extra 1kg30.1-99,999" in row['KG']:
                    extra_30kg_row = pricing_df.iloc[i+2]
        
        area_col = f"area{area}"
        
        # חישוב לפי טווח משקל
        if weight <= 10:
            weights = basic_pricing['KG'].astype(float).tolist()
            closest_weight = min(weights, key=lambda x: abs(x - weight))
            price = basic_pricing[basic_pricing['KG'] == closest_weight][area_col].values[0]
            
        elif weight <= 30:
            base_price = basic_pricing[basic_pricing['KG'] == 10.0][area_col].values[0]
            extra_units = (weight - 10) / 0.5
            price = base_price + (extra_units * extra_10kg_row[area_col])
            
        else:
            base_price = basic_pricing[basic_pricing['KG'] == 30.0][area_col].values[0]
            extra_units = weight - 30
            price = base_price + (extra_units * extra_30kg_row[area_col])
            
        return float(price)
        
    except Exception as e:
        st.error(f"שגיאת DHL: {str(e)}")
        return 0

def calculate_fedex_price(pricing_df, weight, zone):
    """מחשב מחיר FedEx לפי משקל ואזור"""
    try:
        zone_col = f"Zone {zone}"
        
        if weight <= 24:
            weights = pricing_df['KG'].astype(float).tolist()
            closest_weight = min(weights, key=lambda x: abs(x - weight))
            price = pricing_df[pricing_df['KG'] == closest_weight][zone_col].values[0]
            
        else:
            # חיפוש בטבלת IP
            for i, row in pricing_df.iterrows():
                if isinstance(row['KG'], str) and '-' in row['KG']:
                    low, high = map(int, row['KG'].split('-'))
                    if low <= weight <= high:
                        return float(row[zone_col]) * weight
                elif isinstance(row['KG'], str) and '+' in row['KG']:
                    low = int(row['KG'].replace('+', ''))
                    if weight >= low:
                        return float(row[zone_col]) * weight
            
            st.error("לא נמצא תעריף מתאים")
            return 0
            
        return float(price)
    
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
            # מציאת אזורים
            dhl_area = dhl_mapping[dhl_mapping.iloc[:,0] == country].iloc[0,1]
            fedex_zone = fedex_mapping[fedex_mapping.iloc[:,0] == country.split(' (')[0]].iloc[0,1]
            
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
            if dhl_price + fedex_price > 0:
                cheaper = "DHL" if dhl_price < fedex_price else "FedEx"
                price_diff = abs(dhl_price - fedex_price)
                max_price = max(dhl_price, fedex_price)
                savings = (price_diff / max_price) * 100 if max_price != 0 else 0
                st.success(f"✅ {cheaper} חסכון של ${price_diff:.2f} ({savings:.1f}%)")
                
    except Exception as e:
        st.error(f"🚨 שגיאה: {str(e)}")

if __name__ == "__main__":
    main()
