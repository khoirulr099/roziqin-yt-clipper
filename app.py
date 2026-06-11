# ==================== DISPLAY ====================
if "clips_data" in st.session_state and st.session_state.clips_data:
    st.subheader("🎥 Preview & Download")
    cols = st.columns(5)
    for i, data in enumerate(st.session_state.clips_data):
        with cols[i % 5]:
            st.write(f"**{data['name']}**")
            st.video(data["bytes"], format="video/mp4")
            st.download_button(
                f"⬇️ Download {i+1}",
                data=data["bytes"],
                file_name=data["name"],
                mime="video/mp4",
                key=f"dl_{i}"
            )