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
        
        # Get the list of countries with their codes
        country_list = dhl_mapping_df.iloc[:, 0].dropna().tolist()
        
        # User inputs
        selected_country_with_code = st.selectbox("Select Country", country_list)
        weight = st.number_input("Enter Weight (kg)", min_value=0.1, value=15.0, step=0.1)
        
        if st.button("Compare Prices"):
            # Extract the country name without the code
            # This is critical - we need to match exactly what's in the mapping files
            selected_country = selected_country_with_code
            
            # Get the area codes for each courier
            dhl_row = dhl_mapping_df[dhl_mapping_df.iloc[:, 0] == selected_country]
            fedex_row = fedex_mapping_df[fedex_mapping_df.iloc[:, 0] == selected_country]
            
            if not dhl_row.empty and not fedex_row.empty:
                # Get area numbers from the second column
                dhl_area = int(dhl_row.iloc[0, 1])
                fedex_area = int(fedex_row.iloc[0, 1])
                
                # Debugging info to see what was found
                st.info(f"Found DHL area: {dhl_area}, FedEx area: {fedex_area}")
                
                # Find closest weight in pricing table
                weights = pricing_table_df.iloc[:, 0].tolist()
                closest_weight = min(weights, key=lambda x: abs(float(x) - weight))
                weight_row = pricing_table_df[pricing_table_df.iloc[:, 0] == closest_weight]
                
                if not weight_row.empty:
                    # Construct column names for the pricing table
                    dhl_col = f"AREA{dhl_area} DHL"
                    fedex_col = f"AREA{fedex_area} FEDEX"
                    
                    # Get prices
                    if dhl_col in pricing_table_df.columns and fedex_col in pricing_table_df.columns:
                        dhl_price = float(weight_row[dhl_col].values[0])
                        fedex_price = float(weight_row[fedex_col].values[0])
                        
                        # Display results
                        st.subheader("Comparison Results")
                        
                        comparison_df = pd.DataFrame({
                            "Courier": ["DHL", "FEDEX"],
                            "Area": [dhl_area, fedex_area],
                            "Price ($)": [dhl_price, fedex_price]
                        })
                        
                        st.write(f"Shipping from {selected_country}")
                        st.write(f"Weight: {closest_weight}kg")
                        st.dataframe(comparison_df)
                        
                        # Show which is cheaper
                        cheaper = "DHL" if dhl_price < fedex_price else "FEDEX"
                        price_diff = abs(dhl_price - fedex_price)
                        
                        st.success(f"**{cheaper}** is cheaper by **${price_diff:.2f}**")
                    else:
                        st.error(f"Column names not found. Looking for {dhl_col} and {fedex_col}")
                        st.write("Available columns:", pricing_table_df.columns.tolist())
                else:
                    st.error(f"Weight {weight}kg not found in pricing table")
            else:
                # This is where your error is occurring
                st.error(f"Area codes not found for country: {selected_country}.")
                
                # Add debugging to see what's in the mapping files
                st.write("First 10 countries in DHL mapping:", dhl_mapping_df.iloc[:10, 0].tolist())
                st.write("First 10 countries in FedEx mapping:", fedex_mapping_df.iloc[:10, 0].tolist())
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
