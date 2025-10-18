
import streamlit as st
from utils.user import get_user_info

def user_sidebar():
    user, is_logged_in = get_user_info()
    if is_logged_in:
        st.session_state.setdefault("subscription_tier", "Free beta")

    # Sidebar header (brand)
    with st.sidebar:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
              <div style="font-size:22px">🏀</div>
              <div style="font-weight:700;font-size:18px;">EuroGuru</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # User badge / login
        with st.container(border=True):
            if is_logged_in:
                pic = user.get("picture")
                name = user.get("name") or user.get("email") or "User"
                email = user.get("email", "")

                cols = st.columns([1, 3])
                with cols[0]:
                    if pic:
                        st.image(pic, width=44)
                    else:
                        st.markdown(
                            '<div style="font-size:30px;line-height:44px;text-align:center;">👤</div>',
                            unsafe_allow_html=True,
                        )
                with cols[1]:
                    st.markdown(f"**{name}**")
                    if email:
                        st.caption(email)

                st.button("Log out", use_container_width=True, on_click=st.logout)
            else:
                st.markdown("**Not signed in**")
                st.caption("Log in to save preferences and personalize recommendations.")
                st.button("Log in", use_container_width=True, on_click=lambda: st.login("auth0"))

        st.divider()

        # ----- Account / Menu (ready for more items) -----
        st.subheader("Account")
        # Example status chip
        tier = st.session_state.get("subscription_tier", "Guest")
        st.markdown(
            f"""
            <span style="padding:4px 8px;border-radius:999px;border:1px solid #ddd;
                         font-size:12px;background:#f7f7f7;">Plan: <b>{tier}</b></span>
            """,
            unsafe_allow_html=True,
        )

        

        # st.write("")  # spacer
        # menu = st.radio(
        #     "Menu",
        #     ["Overview", "Subscription", "Preferences", "Privacy"],
        #     label_visibility="collapsed",
        # )

        # # Optional: context-specific sidebar content (placeholder)
        # if menu == "Overview":
        #     st.caption("Quick links and recent activity will appear here.")
        # elif menu == "Subscription":
        #     st.caption("Manage your plan and billing (coming soon).")
        #     st.button("Upgrade to Pro", use_container_width=True, disabled=True)
        # elif menu == "Preferences":
        #     st.caption("Personalize recommendations (coming soon).")
        # else:
        #     st.caption("Manage data & export (coming soon).")

        # st.divider()
        # with st.expander("Auth debug"):
        #     st.json(st.experimental_user or {})

        st.divider()

        st.image("images/sidebar_image.png", width=350)