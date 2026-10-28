import streamlit as st
st.title('하늘라룰라룰')
a=st.text_input('이름을 입력하세요!')
b=st.selectbox('좋아하는 음식을 선택하세요',['신라면','새우탕면','열라면'])
if st.button('인사말 생성'):
  st.write('반갑습니다')
  st.info(a+'님, 안녕하세요!')
