from datetime import datetime
import re

import streamlit as st
import pandas as pd

st.set_page_config(page_title='Lídio Matrículas UFABC', page_icon=':books:', layout='wide')


def limpar_nome_disciplina(turma):
    partes = turma.split()  # Divide a string em uma lista de palavras
    for i, palavra in enumerate(partes):
        if 'matutino' in palavra.lower() or 'noturno' in palavra.lower():
            return ' '.join(partes[:i])  # Junta as partes até a palavra identificada
    raise Exception(f"{turma=} {partes=}") #return turma  # Retorna o original se não encontrar "matutino" ou "noturno"


catalogo = pd.read_parquet('disciplinas.parquet')
turmas = pd.read_parquet('matricula_2025_1.parquet')

tab_horarios, tab_disciplinas = st.tabs(['📅 Organizar Horários', '🗃️ Catálogo de Disciplinas'])

with tab_disciplinas:
    with st.expander("Todas as disciplinas"):
        st.dataframe(catalogo, use_container_width=True)
    st.selectbox('Escolha a disciplina', catalogo['DISCIPLINA'].unique(), key='disciplina_selecionada')
    a = catalogo[catalogo['DISCIPLINA'] == st.session_state['disciplina_selecionada']].transpose()
    st.dataframe(a, use_container_width=True)


from itertools import combinations, product


def combinar_horarios(row):
    horarios = []

    # Adicionar horários semanais
    for horario in row['HORÁRIOS.semanal']:
        horario['frequencia'] = 'semanal'
        horarios.append(horario)

    # Adicionar horários quinzenais I
    for horario in row['HORÁRIOS.quinzenal I']:
        horario['frequencia'] = 'quinzenal I'
        horarios.append(horario)

    # Adicionar horários quinzenais II
    for horario in row['HORÁRIOS.quinzenal II']:
        horario['frequencia'] = 'quinzenal II'
        horarios.append(horario)

    return horarios


def eh_compativel(d1: dict, d2: dict) -> bool:
    for h1 in d1['HORÁRIOS']:
        for h2 in d2['HORÁRIOS']:
            if (
                    h1['dia'] == h2['dia'] and
                    (not (h1['frequencia'] == 'quinzenal II' and h2['frequencia'] == 'quinzenal I') or
                     not (h1['frequencia'] == 'quinzenal I' and h2['frequencia'] == 'quinzenal II'))
            ):
                h1_inicio = datetime.strptime(h1['inicio'], '%H:%M')
                h1_fim = datetime.strptime(h1['fim'], '%H:%M')
                h2_inicio = datetime.strptime(h2['inicio'], '%H:%M')
                h2_fim = datetime.strptime(h2['fim'], '%H:%M')

                if h1_inicio < h2_fim and h1_fim > h2_inicio:
                    #st.write(f"{h1_inicio=}, {h1_fim=}, {h2_inicio=}, {h2_fim=}")
                    return False
    return True


@st.cache_data
def gerar_combinacoes_e_testar(lista_dfs: list[pd.DataFrame]) -> list:
    n = len(lista_dfs)
    compativeis = []

    for r in range(2, n + 1):  # De 2 até o total de DataFrames
        for combinacao_dfs in combinations(lista_dfs, r):
            linhas_por_df = [df.to_dict(orient='records') for df in combinacao_dfs]
            for produto in product(*linhas_por_df):
                for a, b in combinations(produto, 2):
                    if not eh_compativel(a, b):
                        break
                else:  # Se não houver incompatibilidade
                    with st.container(border=True):
                        st.dataframe(pd.DataFrame(produto))
                    compativeis.append(produto)

    return compativeis


with tab_horarios:
    turmas['DISCIPLINA'] = turmas['TURMA'].apply(limpar_nome_disciplina)
    with st.expander("Todas as turmas"):
        st.dataframe(turmas, use_container_width=True)

    nomes_disciplinas = turmas['DISCIPLINA'].unique()
    disciplina_possiveis = st.multiselect('Escolha a disciplina', nomes_disciplinas, key='disciplinas_possiveis')
    turmas_correspondentes = []

    for disciplina in disciplina_possiveis:
        turmas_correspondentes.extend(turmas[turmas['DISCIPLINA'] == disciplina].values)

    st.dataframe(turmas_correspondentes, use_container_width=True, selection_mode="multi-row", on_select="rerun",
                 key='index_turmas_posssiveis')

    turmas_possiveis = pd.DataFrame([
        turmas_correspondentes[int(i)] for i in st.session_state['index_turmas_posssiveis']['selection']['rows']
    ])

    try:
        turmas_possiveis.columns = turmas.columns
        #st.dataframe(turmas_possiveis, use_container_width=True)

        turmas_possiveis["HORÁRIOS"] = turmas_possiveis.apply(combinar_horarios, axis=1)
        turmas_possiveis.drop(columns=['HORÁRIOS.semanal', 'HORÁRIOS.quinzenal I', 'HORÁRIOS.quinzenal II'], inplace=True)
        #st.dataframe(turmas_possiveis, use_container_width=True)

        lista_dfs = [grupo.reset_index(drop=True) for _, grupo in turmas_possiveis.groupby('DISCIPLINA')]
        #print(f"{lista_dfs=}")
        texto = st.container()
        comb_possiveis = gerar_combinacoes_e_testar(lista_dfs)
        texto.write(f"Combinacoes possiveis: {len(comb_possiveis)}")

    except Exception as e:
        st.error(e)

    # Gera todas as combinações possíveis de turmas
    #for combo in combinations(turmas_possiveis.to_dict('records'), 2):  # Ajuste para 2 turmas
    #    if all(not verificar_conflito(combo[i], combo[j]) for i in range(len(combo)) for j in range(i + 1, len(combo))):
    #        comb_possiveis.append(combo)

    #st.dataframe(comb_possiveis, use_container_width=True)


#st.write(f"{a}")
