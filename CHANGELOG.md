# **SGT v1.0 Release Notes**

## **Functional Updates:**

1. **Connection State Indicators:**
   - Startup: Displays red.
   - Successful WiFi Connection (Tenda2): Displays green.
   - Updating firmware: Displays yellow.

2. **LED Flow Update:**
   - Transitioned from a three-color system (green for normal, yellow for near congestion, red for congestion) to a gradient scale from green to red, indicating increasing load levels on the cable.

3. **Microgrid Enhancements:**
   - Transformers at connection points between varying voltage levels are now optional.
   - The microgrid functions effectively when there's a balance between supply and demand, even after removing transformers.

4. **Line Breaking Feature:**
   - Ability to disable line cables via the GUI, halting energy flow through that cable section.

## **GUI Applications Improvements:**

1. **Enhanced Physical Model Representation:**
   - One physical model now represents a bus with multiple energy sources.
   - Additional generators and loads can be added and managed via the GUI.

2. **Interactive Physical Model Values:**
   - Physical model values displayed in a table are now modifiable through the GUI.

3. **Transformer Capacity Monitoring:**
   - GUI application now enables checking the remaining capacity of transformers.

4. **Scenario Management:**
   - Easy switching between scenarios (e.g., winter to summer) directly via the GUI, eliminating the need for console commands.

## **Software Backend Enhancements:**

1. **Over-The-Air (OTA) Updates Implemented:**
   - Enables remote software updates.

2. **Dynamic Solar Power Adaptation:**
   - Integration of mini PV for dynamic solar power adjustments.

3. **SGT Dynamic Simulation:**
   - Visualization support with Jupiter Notebook.

4. **User-Level Customization:**
   - Advanced and Admin modes in the GUI for different user expertise levels.

5. **Optimisation:**
   - Improved startup time of the SGT simulation program.
   - Improved communication speed between the Smart Grid Table hardware and the SGT simulation program.
