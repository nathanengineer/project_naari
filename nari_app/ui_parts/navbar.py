import dash_bootstrap_components as dbc

def navbar() -> dbc.Navbar:
    """ Top navigation bar for the N.A.R.I. dashboard. """
    return dbc.Navbar(
        id="navbar_id",
        class_name="px-3",   # small horizontal padding
        children=[
            # Left: Brand
            dbc.NavbarBrand("N.A.R.I Control Panel", class_name="ms-1"),

            # Right: room for controls (theme toggle, etc.)
            dbc.Nav(
                class_name="ms-auto",  # push to the right
                navbar=True,
                children=[
                    # Placeholder theme switch (more complicated than previoulsy thought)
                    dbc.Switch(
                        id="dark_light_switch_id",
                        label="Light/Dark Mode",
                        value=False,
                        class_name="mb-0",
                    ),
                    # Extra Items location place holder
                ],
            ),
        ],
    )
