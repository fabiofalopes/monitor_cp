# Análise do Problema das Cores das Linhas Ferroviárias

## 🚨 Problema Identificado

Actualmente, todas as linhas ferroviárias do mesmo **tipo** (main, regional, urban, freight) têm a mesma cor no mapa, o que torna impossível distinguir entre linhas diferentes. Por exemplo:

- **Linha do Norte** e **Linha do Sul** = ambas verde escuro (#1B5E20) porque são "main"
- **Linha de Cascais** e **Linha de Sintra** = ambas roxo (#6A1B9A) porque são "urban"
- **Linha do Douro** e **Linha da Beira Alta** = ambas azul (#1565C0) porque são "regional"

## 📊 Dados Disponíveis da API OSM

### Nomes de Linhas Identificados (amostra):
```
"Linha da Beira Alta"
"Linha da Beira Baixa" 
"Linha de Cascais"
"Linha de Cintura"
"Linha de Évora"
"Linha de Guimarães"
"Linha de Leixões"
"Linha de Sines"
"Linha de Sintra"
"Linha de Vendas Novas"
"Linha do Alentejo"
"Linha do Algarve"
"Linha do Douro"
"Linha do Leste"
"Linha do Minho"
"Linha do Norte"
"Linha do Oeste"
"Linha do Sul"
```

### Propriedades Úteis para Diferenciação:
- **name**: Nome completo da linha (mais específico)
- **ref**: Referência numérica da linha
- **usage**: main, branch, regional
- **electrified**: contact_line, yes, no
- **maxspeed**: 200, 180, 120, etc.
- **tracks**: 1, 2, 4 (número de vias)
- **operator**: "Infraestruturas de Portugal, S.A.", "CP"

## 🎨 Estratégias para Cores Únicas

### 1. **Hash-based Color Generation** (Já Implementado)
```python
def _generate_unique_color(self, line_name: str) -> str:
    hash_object = hashlib.md5(line_name.encode())
    # Gera cor baseada no hash do nome
```

**Prós**: Cores consistentes para o mesmo nome
**Contras**: Pode gerar cores muito similares ou pouco contrastantes

### 2. **Paleta de Cores Predefinida** (Recomendado)
Criar uma paleta com cores suficientemente distintas e atribuir sequencialmente:

```python
RAILWAY_COLORS = [
    '#E53E3E',  # Vermelho
    '#3182CE',  # Azul
    '#38A169',  # Verde
    '#D69E2E',  # Amarelo/Dourado
    '#805AD5',  # Roxo
    '#DD6B20',  # Laranja
    '#319795',  # Teal
    '#E53E3E',  # Rosa
    '#2D3748',  # Cinzento escuro
    '#744210',  # Castanho
    '#553C9A',  # Índigo
    '#C53030',  # Vermelho escuro
    '#2B6CB0',  # Azul escuro
    '#276749',  # Verde escuro
    '#B7791F',  # Dourado escuro
    '#6B46C1',  # Roxo escuro
]
```

### 3. **Cores por Região Geográfica**
Atribuir cores baseadas na região que a linha serve:

```python
REGION_COLORS = {
    'norte': '#1565C0',      # Azul para Norte
    'centro': '#2E7D32',     # Verde para Centro  
    'lisboa': '#7B1FA2',     # Roxo para Lisboa
    'alentejo': '#F57C00',   # Laranja para Alentejo
    'algarve': '#D32F2F',    # Vermelho para Algarve
    'internacional': '#424242' # Cinzento para internacionais
}
```

### 4. **Cores por Função/Importância**
```python
FUNCTION_COLORS = {
    'intercidades': '#1B5E20',    # Verde escuro - linhas principais
    'regional': '#1565C0',        # Azul - linhas regionais
    'urbano': '#7B1FA2',          # Roxo - linhas urbanas
    'mercadorias': '#E65100',     # Laranja - mercadorias
    'internacional': '#424242',   # Cinzento - internacionais
    'ramal': '#795548'            # Castanho - ramais
}
```

## 🔧 Implementação Recomendada

### Abordagem Híbrida:
1. **Usar paleta predefinida** para linhas principais conhecidas
2. **Fallback para hash-based** para linhas não mapeadas
3. **Garantir contraste mínimo** entre cores adjacentes

```python
def get_line_color(self, line_name: str, line_type: str) -> str:
    # 1. Verificar se é uma linha principal conhecida
    if line_name in KNOWN_LINES_COLORS:
        return KNOWN_LINES_COLORS[line_name]
    
    # 2. Atribuir cor da paleta baseada no índice
    line_index = hash(line_name) % len(RAILWAY_COLORS)
    return RAILWAY_COLORS[line_index]
    
    # 3. Garantir que cores adjacentes são diferentes
    # (implementar lógica de verificação de proximidade geográfica)
```

## 🎯 Mapeamento Específico Sugerido

```python
PORTUGUESE_RAILWAY_COLORS = {
    # Linhas Principais (Intercidades)
    'Linha do Norte': '#1B5E20',        # Verde escuro
    'Linha do Sul': '#D32F2F',          # Vermelho
    'Linha da Beira Alta': '#1565C0',   # Azul
    'Linha do Minho': '#7B1FA2',        # Roxo
    'Linha do Leste': '#F57C00',        # Laranja
    'Linha do Oeste': '#2E7D32',        # Verde
    
    # Linhas Urbanas (Lisboa)
    'Linha de Cascais': '#00ACC1',      # Ciano
    'Linha de Sintra': '#8E24AA',       # Roxo claro
    'Linha de Cintura': '#5E35B1',      # Índigo
    
    # Linhas Regionais
    'Linha do Douro': '#3F51B5',        # Azul índigo
    'Linha do Algarve': '#FF5722',      # Laranja avermelhado
    'Linha do Alentejo': '#795548',     # Castanho
    'Linha da Beira Baixa': '#607D8B',  # Azul acinzentado
    'Linha de Évora': '#9C27B0',        # Magenta
    'Linha de Guimarães': '#4CAF50',    # Verde claro
    'Linha de Leixões': '#FF9800',      # Âmbar
    'Linha de Sines': '#E91E63',        # Rosa
    'Linha de Vendas Novas': '#009688', # Teal
    
    # Linhas Internacionais
    'Linha Internacional Elvas - Badajoz': '#424242',           # Cinzento
    'Linha Internacional Vilar Formoso - Fuentes de Oñoro': '#616161', # Cinzento claro
}
```

## 🚀 Próximos Passos

1. **Implementar paleta de cores específica** para linhas portuguesas conhecidas
2. **Testar contraste visual** no mapa com dados reais
3. **Adicionar legenda** no mapa para identificar as cores
4. **Considerar acessibilidade** (daltonismo) na escolha das cores
5. **Documentar mapeamento** para futuras manutenções

## 🔍 Considerações Técnicas

- **Performance**: Manter cache de cores para evitar recálculos
- **Consistência**: Garantir que a mesma linha tem sempre a mesma cor
- **Escalabilidade**: Sistema deve funcionar com novas linhas descobertas
- **Manutenibilidade**: Facilitar alterações futuras na paleta de cores 