import streamlit as st
import pandas as pd

def main():
    st.title("Shipping Price Comparison Tool")
    
    # Hardcoded file paths
    dhl_mapping_path = "dhl pricing.xlsx"  # Replace with your actual path
    fedex_mapping_path = "fedex pricing.xlsx"  # Replace with your actual path
    pricing_table_path = "pricing table.xlsx"  # Replace with your actual path
    
    try:
        # Load DHL mapping data
        dhl_mapping_df = pd.read_csv(dhl_mapping_path)
        st.sidebar.success("DHL mapping data loaded successfully")
        
        # Load FedEx mapping data
        fedex_mapping_df = pd.read_csv(fedex_mapping_path)
        st.sidebar.success("FedEx mapping data loaded successfully")
        
        # Load pricing table data
        pricing_table_df = pd.read_csv(pricing_table_path)
        st.sidebar.success("Pricing table data loaded successfully")
        
        # User inputs
        country = st.selectbox("Select Country", dhl_mapping_df.iloc[:, 0].unique())
        weight = st.number_input("Enter Weight (kg)", min_value=0.1, step=0.1)
        
        if st.button("Compare Prices"):
            # Get DHL and FedEx area codes for the selected country
            dhl_area_row = dhl_mapping_df[dhl_mapping_df.iloc[:, 0] == country]
            fedex_area_row = fedex_mapping_df[fedex_mapping_df.iloc[:, 0] == country]
            
            if not dhl_area_row.empty and not fedex_area_row.empty:
                dhl_area_code = int(dhl_area_row.iloc[0, 1])  # Second column contains area codes
                fedex_area_code = int(fedex_area_row.iloc[0, 1])  # Second column contains area codes
                
                # Find the closest weight in the pricing table
                weights_list = pricing_table_df.iloc[:, 0].tolist()  # First column contains weights
                closest_weight = min(weights_list, key=lambda x: abs(x - weight))
                weight_row = pricing_table_df[pricing_table_df.iloc[:, 0] == closest_weight]
                
                if not weight_row.empty:
                    # Get DHL and FedEx prices for the respective areas
                    dhl_price_col = f"AREA{dhl_area_code} DHL"
                    fedex_price_col = f"AREA{fedex_area_code} FEDEX"
                    
                    if dhl_price_col in weight_row.columns and fedex_price_col in weight_row.columns:
                        dhl_price = weight_row.iloc[0][dhl_price_col]
                        fedex_price = weight_row.iloc[0][fedex_price_col]
                        
                        # Display results
                        st.subheader("Comparison Results")
                        comparison_data = {
                            "Courier": ["DHL", "FEDEX"],
                            "Price": [dhl_price, fedex_price]
                        }
                        comparison_df = pd.DataFrame(comparison_data)
                        cheaper_courier = "DHL" if dhl_price < fedex_price else "FEDEX"
                        price_diff = abs(dhl_price - fedex_price)
                        
                        st.write(f"Shipping from {country} - Weight: {closest_weight}kg")
                        st.dataframe(comparison_df)
                        
                        st.success(f"**{cheaper_courier}** is cheaper by **${price_diff:.2f}**")
                        
                    else:
                        st.error("Pricing columns not found in table.")
                else:
                    st.error("Weight not found in the table.")
            else:
                st.error(f"Area codes not found for country: {country}.")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
