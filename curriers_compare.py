import pandas as pd
import streamlit as st

def main():
    st.title("Shipping Price Comparison Tool")
    
    # Hardcoded file paths
    dhl_mapping_path = "dhl pricing.xlsx"
    fedex_mapping_path = "fedex pricing.xlsx"
    pricing_table_path = "pricing table.xlsx"
    
    try:
        # Load all data files
        dhl_mapping_df = pd.read_excel(dhl_mapping_path)
        fedex_mapping_df = pd.read_excel(fedex_mapping_path)
        pricing_table_df = pd.read_excel(pricing_table_path)
        
        st.sidebar.success("DHL mapping data loaded successfully")
        st.sidebar.success("FedEx mapping data loaded successfully")
        st.sidebar.success("Pricing table data loaded successfully")
        
       # Create dictionaries for easy lookup
        # For DHL: Map from "Country (Code)" to area number
        dhl_areas = {country: int(area) for country, area in zip(dhl_mapping_df.iloc[:, 0], dhl_mapping_df.iloc[:, 1])}
        
        # Create a version of country names without codes for FedEx mapping
        country_map = {}
        for full_name in dhl_mapping_df.iloc[:, 0]:
            if "(" in full_name and ")" in full_name:
                # Extract the country name without the code
                simple_name = full_name.split(" (")[0].strip()
                country_map[full_name] = simple_name
        
        # User inputs
        selected_country = st.selectbox("Select Country", sorted(dhl_areas.keys()))
        weight = st.number_input("Enter Weight (kg)", min_value=0.1, value=5.0, step=0.1)
        
        if st.button("Compare Prices"):
            # Get DHL area
            dhl_area = dhl_areas.get(selected_country)
            
            # For FedEx, try to find the corresponding country without code
            simple_country_name = country_map.get(selected_country, selected_country)
            fedex_row = fedex_mapping_df[fedex_mapping_df.iloc[:, 0] == simple_country_name]
            
            if dhl_area is not None and not fedex_row.empty:
                # Get FedEx area
                fedex_area = int(fedex_row.iloc[0, 1])
                
                # Find closest weight in pricing table
                weights_list = pricing_table_df.iloc[:, 0].tolist()
                closest_weight = min(weights_list, key=lambda x: abs(float(x) - weight))
                weight_row = pricing_table_df[pricing_table_df.iloc[:, 0] == closest_weight]
                
                if not weight_row.empty:
                    # Get column names for pricing
                    dhl_col = f"AREA{dhl_area} DHL"
                    fedex_col = f"AREA{fedex_area} FEDEX"
                    
                    if dhl_col in pricing_table_df.columns and fedex_col in pricing_table_df.columns:
                        # Get prices
                        dhl_price = float(weight_row[dhl_col].values[0])
                        fedex_price = float(weight_row[fedex_col].values[0])
                        
                        # Display results
                        st.subheader("Comparison Results")
                        
                        comparison_data = {
                            "Courier": ["DHL", "FEDEX"],
                            "Area": [dhl_area, fedex_area],
                            "Price ($)": [dhl_price, fedex_price]
                        }
                        
                        comparison_df = pd.DataFrame(comparison_data)
                        st.write(f"Shipping from {selected_country}")
                        st.write(f"Weight: {closest_weight}kg")
                        st.dataframe(comparison_df)
                        
                        # Show which is cheaper
                        cheaper_courier = "DHL" if dhl_price < fedex_price else "FEDEX"
                        price_diff = abs(dhl_price - fedex_price)
                        savings_percent = (price_diff / max(dhl_price, fedex_price)) * 100
                        
                        st.success(f"**{cheaper_courier}** is cheaper by **${price_diff:.2f}** ({savings_percent:.1f}%)")
                    else:
                        st.error(f"Price columns not found in pricing table.")
                else:
                    st.error(f"Weight {weight}kg not found in pricing table.")
            else:
                st.error(f"Area codes not found for country: {selected_country}.")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
