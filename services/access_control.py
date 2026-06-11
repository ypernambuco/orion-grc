from html import escape

import streamlit as st


ACTIVE_PROFILE_KEY = "orion_active_profile"

PROFILE_PERMISSIONS = {
    "Admin": {"Dashboard", "Áreas", "Documentos", "Riscos", "Evidências"},
    "Compliance": {"Dashboard", "Áreas", "Documentos", "Evidências"},
    "Gestor": {"Dashboard", "Áreas", "Documentos", "Riscos"},
    "Diretoria": {"Dashboard"},
    "Auditoria": {"Dashboard", "Evidências"},
}

PROFILE_DESCRIPTIONS = {
    "Admin": "Acesso total aos módulos operacionais.",
    "Compliance": "Governança documental, áreas e evidências.",
    "Gestor": "Gestão operacional de áreas, documentos e riscos.",
    "Diretoria": "Leitura exclusiva do Dashboard executivo.",
    "Auditoria": "Consulta executiva e gestão de evidências.",
}


def get_profiles() -> list[str]:
    return list(PROFILE_PERMISSIONS)


def get_active_profile() -> str:
    profile = st.session_state.get(ACTIVE_PROFILE_KEY, "Admin")
    if profile not in PROFILE_PERMISSIONS:
        profile = "Admin"
        st.session_state[ACTIVE_PROFILE_KEY] = profile
    return profile


def set_active_profile(profile: str) -> None:
    if profile not in PROFILE_PERMISSIONS:
        raise ValueError(f"Perfil desconhecido: {profile}")
    st.session_state[ACTIVE_PROFILE_KEY] = profile


def get_allowed_modules(profile: str | None = None) -> set[str]:
    selected_profile = profile or get_active_profile()
    return set(PROFILE_PERMISSIONS.get(selected_profile, set()))


def has_permission(module: str, profile: str | None = None) -> bool:
    if module == "Início":
        return True
    return module in get_allowed_modules(profile)


def require_permission(module: str) -> None:
    if has_permission(module):
        return

    profile = escape(get_active_profile())
    safe_module = escape(module)
    st.markdown(
        f"""
        <div class="orion-empty-state">
            <div class="orion-empty-kicker">Controle de acesso</div>
            <div class="orion-empty-title">Acesso não autorizado</div>
            <div class="orion-empty-message">
                O perfil ativo <strong>{profile}</strong> não possui permissão
                para acessar o módulo {safe_module}.
            </div>
            <div class="orion-empty-action">
                Selecione outro perfil demo na sidebar para validar uma permissão diferente.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()
