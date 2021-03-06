import yfinance
import models
from fastapi import Depends, FastAPI, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from models import Stock


templates = Jinja2Templates(directory='templates')

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

class StockRequest(BaseModel):
    symbol: str


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get('/')
async def dashboard(request: Request):
    return templates.TemplateResponse('dashboard.html', {'request': request})


def fetch_stock_data(id: int):
    db = SessionLocal()
    stock = db.query(Stock).filter(Stock.id==id).first()

    yahoo_data = yfinance.Ticker(stock.symbol)

    stock.ma200 = yahoo_data.info['twoHundredDayAverage']
    stock.ma50 = yahoo_data.info['fiftyDayAverage']
    stock.price = yahoo_data.info['previousClose']
    stock.forward_pe = yahoo_data.info['forwardPE']
    stock.forward_eps = yahoo_data.info['forwardEps']
    stock.dividend_yield = yahoo_data.info['dividendYield'] * 100

    db.add(stock)
    db.commit()


@app.post('/post/new')
async def create_stock(stock_request: StockRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):

    stock = Stock()
    stock.symbol = stock_request.symbol
    db.add(stock)
    db.commit()

    background_tasks.add_task(fetch_stock_data, stock.id)

    return {
        'code': 'success',
        'message': 'Stock Created',
    }
