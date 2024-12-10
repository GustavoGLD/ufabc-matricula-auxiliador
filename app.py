from datetime import datetime
import re

import streamlit as st
import pandas as pd
from numpy import ndarray

CATALOGO_PATH = 'disciplinas.parquet'
PLANILHA_PATH = 'matricula_2025_1.parquet'

st.set_page_config(
    page_title='Lídio Matrículas UFABC',
    page_icon=':books:',
    layout='wide'
)


def limpar_nome_disciplina(turma):
    partes = turma.split()  # Divide a string em uma lista de palavras
    for i, palavra in enumerate(partes):
        if 'matutino' in palavra.lower() or 'noturno' in palavra.lower():
            return ' '.join(partes[:i])  # Junta as partes até a palavra identificada
    raise Exception(f"{turma=} {partes=}")  # return turma  # Retorna o original se não encontrar "matutino" ou "noturno"


class MainView:
    def __init__(self, cnt=st.container(border=True)):
        (self.tab_horarios, self.tab_catalogo) = cnt.tabs(
            [
                '📅 Encaixar Turmas',
                '🗃️ Catálogo de Disciplinas'
            ]
        )


class CatalogoView:
    def __init__(self, cnt=st.container(border=True)):
        with cnt:
            self.cnt_disciplinas = st.container()
            self.cnt_selecionar_disciplinas = st.container()
            self.cnt_info_disciplina = st.container()

    def view_disciplinas(self, catalogo: pd.DataFrame):
        self.cnt_disciplinas.dataframe(catalogo, use_container_width=True)

    def view_selecionar_disciplina(self, catalogo: pd.DataFrame):
        self.cnt_selecionar_disciplinas.selectbox('Escolha a disciplina', catalogo['DISCIPLINA'].unique(),
                                                  key='disciplina_selecionada')

    def view_infos(self, turmas: pd.DataFrame):
        self.cnt_info_disciplina.dataframe(turmas, use_container_width=True)


class CatalogoController:
    def __init__(self, main_view: MainView):
        self.catalogo_view = CatalogoView(main_view.tab_catalogo)

    def run(self):
        catalogo = pd.read_parquet(CATALOGO_PATH)
        self.catalogo_view.view_disciplinas(catalogo)
        self.catalogo_view.view_selecionar_disciplina(catalogo)
        disciplina = catalogo[catalogo['DISCIPLINA'] == st.session_state['disciplina_selecionada']].transpose()
        self.catalogo_view.view_infos(disciplina)


class EnturmadorView:
    def __init__(self, cnt=st.container(border=True)):
        with cnt:
            with st.expander("Todas as turmas"):
                self.cnt_disciplinas = st.container()
            self.cnt_disciplinas_selecionadas = st.container()

    def view_disciplinas(self, catalogo: pd.DataFrame):
        self.cnt_disciplinas.dataframe(catalogo, use_container_width=True)

    def view_disciplinas_selecionadas(self, disciplinas: ndarray):
        self.cnt_disciplinas_selecionadas.multiselect(
            'Escolha a disciplina', disciplinas, key='disciplinas_selecionadas'
        )


class EnturmadorController:
    def __init__(self, main_view: MainView):
        self.enturmador_view = EnturmadorView(main_view.tab_horarios)

    def run(self):
        turmas = pd.read_parquet(PLANILHA_PATH)
        turmas['DISCIPLINA'] = turmas['TURMA'].apply(limpar_nome_disciplina)
        self.enturmador_view.view_disciplinas(turmas)

        nomes_disciplinas = turmas['DISCIPLINA'].unique()
        self.enturmador_view.view_disciplinas_selecionadas(nomes_disciplinas)


class MainController:
    def __init__(self):
        self.main_view = MainView()
        self.catalogo = CatalogoController(self.main_view)
        self.enturmador = EnturmadorController(self.main_view)

    def run(self):
        self.catalogo.run()
        self.enturmador.run()


if __name__ == '__main__':
    MainController().run()
