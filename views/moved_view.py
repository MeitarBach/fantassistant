import streamlit as st

NEW_APP_URL = "https://www.eurogurufantasy.com"


def moved_view():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
        .moved-hero { text-align: center; padding-top: 8px; }
        .moved-hero h1 { font-size: 2.6rem; margin-bottom: 0.2rem; }
        .moved-hero .tagline { font-size: 1.25rem; opacity: 0.8; margin-bottom: 1.5rem; }
        .moved-features {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px; margin: 1.5rem 0 2rem;
        }
        .moved-feature {
            border: 1px solid rgba(128,128,128,0.25); border-radius: 12px;
            padding: 14px 16px; text-align: left;
        }
        .moved-feature .icon { font-size: 1.5rem; }
        .moved-feature b { display: block; margin: 4px 0 2px; }
        .moved-feature span { font-size: 0.9rem; opacity: 0.8; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, logo_col, _ = st.columns([1, 1, 1])
    with logo_col:
        st.image("images/logo.png", use_container_width=True)

    st.markdown(
        """
        <div class="moved-hero">
          <h1>🏀 EuroGuru has leveled up!</h1>
          <div class="tagline">
            New home. New look. Same obsession with building the perfect Euroleague Fantasy roster.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        We've taken everything you loved about EuroGuru (the stats, the injury reports,
        the lineup recommendations) and rebuilt it from the ground up.
        **The new EuroGuru is faster, smarter, and way easier to use.**
        This version is retired and won't get new updates, so jump over to the new app
        and keep your edge for the next round.
        """
    )

    st.markdown(
        """
        <div class="moved-features">
          <div class="moved-feature"><div class="icon">⚡</div><b>Blazing fast</b><span>Stats and rankings load in a snap.</span></div>
          <div class="moved-feature"><div class="icon">🎨</div><b>Fresh UX</b><span>A clean, modern design built for desktop and mobile.</span></div>
          <div class="moved-feature"><div class="icon">🧠</div><b>Smarter picks</b><span>Improved recommendations to help you win your league.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.link_button(
        "🚀 Take me to the new EuroGuru",
        NEW_APP_URL,
        type="primary",
        use_container_width=True,
    )
    st.caption(f"Update your bookmarks: [eurogurufantasy.com]({NEW_APP_URL})")
