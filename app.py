from numpy.lib import index_tricks
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def style(df):
    copy=df.copy()
    if copy.equals(portfolio):
        copy.index = copy.index+1
        copy["Initial Price"]=copy["Initial Price"].map('${:}'.format)
        copy["Current Price"]=copy["Current Price"].map('${:.2f}'.format)
        copy["P/L"]=copy["P/L"].map('${:.2f}'.format)

        copy["Proportion"]=copy["Proportion"].map(lambda x: "{0:.2f}%".format(x*100))
    elif copy.equals(total):
        copy.index=[""]
        copy["Total P/L"]=copy["Total P/L"].map('${:.2f}'.format)
        copy["Total Investing"]=copy["Total Investing"].map('${:}'.format)
        copy["Total Proportion"]=copy["Total Proportion"].map(lambda x: "{0:.2f}%".format(x*100))
    elif copy.equals(cash):
        copy.index=[""]
        copy["Cash Remaining"]=copy["Cash Remaining"].map('${:}'.format)
        copy["Cash Proportion"]=copy["Cash Proportion"].map(lambda x: "{0:.2f}%".format(x*100))
    elif copy.equals(statistics):
        copy.index=[""]
        copy["Alpha"]=copy["Alpha"].map('{:.4f}%'.format)
        copy["Standard Deviation"]=copy["Standard Deviation"].map(lambda x: "{0:.3f}%".format(x*100))
        copy["Batting Average"]=copy["Batting Average"].map(lambda x: "{:.2f}%".format(x))

    return copy


st.header("Portfolio Construction")
initial=st.number_input("Enter the total capital of your portfolio (in $USD, including cash)")
n=st.number_input("Enter the number of stocks you have in your portfolio (10 at max)",min_value=1,max_value=10,step=1)

col1, col2,col3 = st.beta_columns(3)
col1.write("Stock/Fund Ticker")
col2.write("Initial Price")
col3.write("Amount")
dataset_ticker={}
dataset_price={}
dataset_amount={}
dataset=None
for i in range(n):
    dataset_ticker[i]=col1.text_input("",key=i)
    dataset_price[i]=col2.number_input("",key=i)
    dataset_amount[i]=col3.number_input("",min_value=1,step=1,key=i)
pressed=st.button("Construct Portfolio")
if pressed:
    dataset=pd.DataFrame({"Stock/Fund Ticker":list(dataset_ticker.values()),"Initial Price":list(dataset_price.values()),"Amount":list(dataset_amount.values())})

    portfolio=dataset
    st.header("Initial Investment")
    st.subheader("$"+str(initial)+" USD")
    st.header("Portfolio")
    portfolio["Proportion"]=portfolio["Initial Price"]*portfolio["Amount"]/initial

    total=pd.DataFrame({"Total Investing":sum(portfolio["Initial Price"]*portfolio["Amount"]),"Total Proportion":sum(portfolio["Proportion"])},index=[0])
    cash=pd.DataFrame({"Cash Remaining":initial-total["Total Investing"],"Cash Proportion":1-total["Total Proportion"]})

    pie=portfolio.iloc[:,0:3]
    pie["Investing"]=pie["Initial Price"]*pie["Amount"]
    pie=pie[["Stock/Fund Ticker","Investing"]]
    pie=pie.append(pd.DataFrame({"Stock/Fund Ticker":"Cash","Investing":cash["Cash Remaining"]}))
    fig=px.pie(pie, values='Investing', names='Stock/Fund Ticker', title='Portfolio Proportions')
    st.plotly_chart(fig)
    portfoliotable=st.empty()
    totaltable=st.empty()
    cashtable=st.empty()


    import yfinance as yf
    from datetime import date,datetime,timedelta
    today = str(date.today())
    tickerDf={}
    displayDf={}
    portfolioDf={}
    yesterdayclose=[None]*len(portfolio)
    for index,value in portfolio["Stock/Fund Ticker"].items():
        tickerSymbol = value
        st.subheader(tickerSymbol)
        tickerData = yf.Ticker(tickerSymbol)
        displayDf[index] = tickerData.history(period='1d', start=str(date.today()-timedelta(days=5)), end=today)
        tickerDf[index] = tickerData.history(period='1d', start=str(date.today()-timedelta(days=365)), end=today)
        displayDf[index] = displayDf[index].rename(index = lambda x:x.strftime("%Y-%m-%d"))
        

        st.table(displayDf[index].iloc[:,0:4])
        portfolioDf[index]=tickerDf[index].iloc[0:len(tickerDf[index]),0:4]
        portfolioDf[index] = portfolioDf[index].rename(index = lambda x:x.strftime("%Y-%m-%d"))
        s=portfolio["Amount"]
        portfolioDf[index]["Open"]=portfolioDf[index]["Open"]*s[index]
        portfolioDf[index]["High"]=portfolioDf[index]["High"]*s[index]
        portfolioDf[index]["Low"]=portfolioDf[index]["Low"]*s[index]
        portfolioDf[index]["Close"]=portfolioDf[index]["Close"]*s[index]
        yesterdayclose[index]=tickerDf[index].tail(1)["Close"].values


    st.subheader("Portfolio Total")
    totalDf=portfolioDf[0].copy()
    for i in range(len(portfolio)-1):
        totalDf=totalDf.add(portfolioDf[i+1], fill_value=0)
        
    candle = go.Figure(data=[go.Candlestick(x=totalDf.index,
                    open=totalDf['Open'],
                    high=totalDf['High'],
                    low=totalDf['Low'],
                    close=totalDf['Close'])])

    st.plotly_chart(candle)
    st.table(totalDf.tail())
    yesterdayclose = [list(x) for x in yesterdayclose]
    yesterdayclose = [item for sublist in yesterdayclose for item in sublist]
    if len(yesterdayclose)<len(portfolio):
        yesterdayclose+=[None]*(len(portfolio)-len(yesterdayclose))
    portfolio["Current Price"]=yesterdayclose
    portfolio["P/L"]=(portfolio["Current Price"]-portfolio["Initial Price"])*portfolio["Amount"]
    portfolio=portfolio[["Stock/Fund Ticker","Initial Price","Current Price","Amount","Proportion","P/L"]]
    total=pd.DataFrame({"Total P/L":np.nansum(portfolio["P/L"]),"Total Investing":sum(portfolio["Initial Price"]*portfolio["Amount"]),"Total Proportion":sum(portfolio["Proportion"])},index=[0])
    portfoliotable.table(style(portfolio))
    totaltable.table(style(total))
    cashtable.table(style(cash))


    totalDf_pctchange=totalDf["Close"].pct_change()
    std=np.std(totalDf_pctchange)
    tickerData = yf.Ticker("QQQ")
    QQQ = tickerData.history(period='1d', start=str(date.today()-timedelta(days=365)), end=today)
    r=np.corrcoef(QQQ["Close"],totalDf["Close"])
    QQQ_pctchange=QQQ["Close"].pct_change()
    QQQstd=np.std(QQQ_pctchange)
    beta=r[0,1]*std/QQQstd
    QQQ_yrdiff=(QQQ["Close"][-1]-QQQ["Close"][0])/QQQ["Close"][0]*100
    totalDf_yrdiff=(totalDf["Close"][-1]-totalDf["Close"][0])/totalDf["Close"][0]*100
    riskfree=1.13
    alpha=totalDf_yrdiff-riskfree-beta*(QQQ_yrdiff-riskfree)
    success=totalDf_pctchange>QQQ_pctchange
    success=success.tolist()
    batting=success.count(1)/len(success)*100
    statistics=pd.DataFrame({"Standard Deviation":std,"Beta":beta,"Alpha":alpha,"Batting Average":batting},index=[0])
    st.subheader("Portfolio Statistics")
    st.table(style(statistics))