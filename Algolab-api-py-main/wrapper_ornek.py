from algolab import API
from datetime import datetime, timezone, timedelta
import time
from config import *
import pandas as pd, numpy as np, json, os

############################################ ENDPOINT Fonksiyonlari ##################################################
### Emir Gönderme Fonksiyonları
#### Emir Gönderme
def send_order(symbol:str, direction:str, pricetype:str, price:str, lot:str, sms:bool = False, email:bool = False, subaccount:str = "") -> str:
    """
        Attributes:
        :String symbol: Sembol Kodu
        :String direction:  - İşlem Yönü: Buy / Sell (Aliş/Satiş)
        :String pricetype:  - Emir Tipi: piyasa/limit.(Piyasa emri ise fiyat girilmez.)
        :String price:      - Emir tipi limit ise fiyat girilmelidir. (Örn. 1.98 şeklinde girilmelidir.)
        :String lot:        - Emir Adeti
        :Bool sms:          - Sms Gönderim
        :Bool email:        - Email Gönderim
        :String subAccount: - Alt Hesap Numarasi “Boş gönderilebilir. Boş gönderilir ise Aktif Hesap Bilgilerini getirir.”
        *******************************************************************************************************************
        
        Request Parameters: 
        Example of Body: 
        {  
            "symbol":"TSKB",  
            "direction":"Buy"/"Sell",  
            "pricetype":"limit"/"piyasa",  
            "price":"2.01", # pricetype "piyasa" ise fiyat girilmez.  
            "lot":"1",  
            "sms":true,  
            "email":false,  
            "Subaccount":""  
        }

        Output:
        Example of Response: 
        {  
            "success": true,  
            "message": "",  
            "content": "Referans Numaranız: 001VEV;0000-2923NR-IET - HISSEOK"  
        }
        Emir numarasını almak için kod: content.split(" ")[2].split(";")[0]
    """
    if pricetype=='piyasa':
        price=""

    send_order = Conn.SendOrder(symbol = symbol, direction = direction, pricetype = pricetype, price = price, lot = lot ,sms = sms, email = email, subAccount = subaccount)
    print("\nEmir gönderme isteği atılıyor...\n")    
    if send_order:
        try:
            succ = send_order["success"]
            if succ:
                content = send_order["content"]
                # use this debug line to see the content of the response for logging purposes in case of an error
                print(f"Emir İletildi, Dönen cevap: {content}")
                # return id of the order to use in modify and delete functions
                order_id = content.split(" ")[2].split(";")[0] 
                return order_id
            # use this debug line to see the content of the response for logging purposes in case of an error
            else: print(f"Gönderilen emir başarısız. Algolab mesajı: {send_order['message']}") 
        except Exception as e:
            # use this debug line to see the content of the response for logging purposes in case of an error
            print(f"Gönderilen emir ile ilgili hata oluştu: {e}")
#### Emir Düzeltme
def modify_order(id:str, price:str, lot:str = "", viop:bool = False, subaccount:str = "") -> bool:
    """
    :String id:         - Emrin ID’ si
    :String price:      - Düzeltilecek Fiyat
    :String lot:        - Lot Miktari (Sadece emir bir viop emri ise girilmelidir. Aksi halde "" gönderilir.)
    :Bool viop:         - Emrin Viop emri olup olmadığını belirtir. “Viop emri ise true olmalidir.”
    :String subAccount: - Alt Hesap Numarasi “Boş gönderilebilir. Boş gönderilir ise Aktif Hesap Bilgilerini getirir.”
    
    Request Parameters:
    Example of Body:
    {
        "id":"001VEV",
        "price":"2.04",
        "lot":"0",
        "viop":false,
        "subAccount":""
    }

    Output:
    Example of Response:
    {  
        "success": true,  
        "message": "IYILESOK",  
        "content": {  
        "message": "IYILESOK",  
        "duration": "-"  
    } 
    """
    modify_order=Conn.ModifyOrder(id=id,price=price,lot=lot,viop=viop,subAccount="")
    print("\nEmir değiştirme isteği atılıyor...\n")
    if viop:
        lot = lot
    else:
        lot = ""
    if modify_order:
        try:
            succ = modify_order["success"]
            if succ:
                content = modify_order["content"]
                print(f"Emir Düzeltildi: {modify_order['message']}")
                #return content["message"]
                return True
            else: 
                print(content["message"])
                return False 
        except Exception as e:
            print(f"Hata oluştu: {e}")
#### Emir Silme
def delete_order(id:str, subaccount:str = ""):
    """
    Attributes:
    :String id:         - Emrin ID’ si
    :String subAccount: - Alt Hesap Numarasi “Boş gönderilebilir. Boş gönderilir ise Aktif Hesap Bilgilerini getirir.”
    
    Request Parameters:
    Example of Body:
    {
        "id":"001VEV",
        "subAccount":""
    }

    Output:
    Example of Response: 
    {  
        "success": true,  
        "message": "Success",  
        "content": {  
        "message": "Success",  
        "duration": "-"  
    } 
    """
    delete_order = Conn.DeleteOrder(id = id, subAccount = subaccount)
    print("\nEmir silme isteği atılıyor...\n")
    if delete_order:
        try:
            succ = delete_order["success"]
            if succ:
                content = delete_order["content"]
                print(f"Emir Silindi: {delete_order['message']}")
                #return content
                return True
            else: 
                print(f"Emir silme işlemi başarısız: {content['message']}") 
                return False
        except Exception as e:
            print(f"Emir silme işlemiminde hata oluştu: {e}")

# ******************************************************************************************************************************

# REQUESTS
### Sembol Bilgileri
#### Sembole Ait Son 250 OHLCV Datasını Getirme 
def get_candle_data(symbol:str, period:str):
    """
        Belirlediğiniz sembole ait son 250 barlık OHLCV barlarını getirir.
        symbol: Sembol kodu
        period: İstenilen bar periyodu dakikalık olarak girilir.(1,2,5,10,15,30,
        60(1 saatlik için),
        120(2 saatlik için),
        180(3 saatlik için),
        240(4 saatlik için),
        480(8 saatlik için),
        1440(Günlük için), 
        10080(Haftalık için), 
        43200(Aylık için))

        Örnek Body:
        {
            "symbol": "TSKB",
            "period": "1440",
        }
    """
    candle = Conn.GetCandleData(symbol, period)
    print("\nOHLCV barları verisi görüntüleme isteği atılıyor...\n")    
    if candle:
        try:
            succ = candle["success"]
            if succ:
                ohlcv = []
                content = candle["content"]
                #print(f"OHLCV barları verisi: {content}")
                for item in content:
                    dt_str = item["date"]
                    try:
                        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M:%S")

                    ohlcv.append([dt, item["open"], item["high"], item["low"], item["close"], item["volume"]])
                # oluşturduğumuz listi pandas dataframe'e aktariyoruz
                df = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"], data=np.array(ohlcv))
                """
                # dataframe'i json formatına dönüştürüyoruz
                json_data=df.to_json(orient='records')
                # json formatında dosyaya yazdırma
                with open(symbol+period+'.json', 'w', encoding='utf-8') as f:
                    f.write(json_data)
                """
                # print(df.tail())
                return df

            else: print(f"OHLCV barları getirme isteği hatayla sonuçlandı: {candle['message']}") 
        except Exception as e:
            print(f"OHLCV barları getirilirken hata oluştu: {e}")
#### Sembol Bilgisi Getirme
def get_equity_info(symbol:str):
    """
        Sembolle ilgili tavan taban yüksek düşük anlık fiyat gibi bilgileri çekebilirsiniz.
        :String symbol: Sembol Kodu Örn: ASELS
    """
    print("\nSembol bilgisi görüntüleme isteği atılıyor...\n")
    symbol_price_info=Conn.GetEquityInfo(symbol=symbol)
    if symbol_price_info:
        try:
            succ = symbol_price_info["success"]
            if succ:
                content = symbol_price_info["content"]
                df = pd.DataFrame(content,index=[0])
                #print(df)
                return df
            else: print(f"Sembole ait anlık fiyat bilgisi çekme işlemi başarısız: {symbol_price_info['message']}") 
        except Exception as e:
            print(f"Sembolle ait anlık fiyat bilgileri çekme hatası oluştu: {e}")

### result bilgisi
#### Pörtfoy Bilgisi Getirme
def get_instant_position(subaccount:str = ""):
    """
        Yatırım Hesabınıza bağlı alt hesapları (101, 102 v.b.) ve limitlerini görüntüleyebilirsiniz. 
        Portföy bilgilerinizi görüntüleyebilirsiniz.
        sub_account="" varsayılan olarak boş gönderilir.

        Örnek çıktı:
         maliyet  totalstock   code                       profit              cost unitprice totalamount tlamaount explanation type total
0                 0           0      -                            -           9406.07         0           0         0       total    0     0
1             22.96   44.000000  BMSCH             -17.600000000000             22.96     22.56                992.64       BMSCH   CH     0
2             49.98   25.000000  BMSTL              -8.000000000000             49.98     49.66                1241.5       BMSTL   CH     0
3              20.9   48.000000   ESEN             -21.120000000000              20.9     20.46                982.08        ESEN   CH     0
4             10.12  100.000000  EYGYO             -13.000000000000             10.12      9.99                   999       EYGYO   CH     0
5              13.7   73.000000  HATEK               2.920000000000              13.7     13.74               1003.02       HATEK   CH     0
6                 0           0    TRY                            0                 0         1                659.83         TRY   CA     0
7  130.928571428571   28.000000  VAKKO  -137.9999999999880000000000  130.928571428571       126                  3528       VAKKO   CH     0
    """ 
    print("\nPortöy görüntüleme isteği atılıyor...\n")
    instant_position = Conn.GetInstantPosition(sub_account=subaccount)
    if instant_position:
        try:
            succ = instant_position["success"]
            if succ:
                content = instant_position["content"]
                df = pd.DataFrame(content)
                #print(df)
                return df
            else: 
                print(f"Portföy bilgisi alma başarısız: {instant_position['message']}") 
        except Exception as e:
            print(f"Portfoy bilgileri alınırken hata oluştu: {e}")
#### Hesap Bilgisi Getirme
def get_subaccounts():
    """
    Alt hesap bilgilerinizi görüntüleyebilirsiniz. Varsayılan olak boş gönderilirse aktif hesap bilgilerini getirir.
    subAccount: Alt hesap numarası. Örn: 101, 102, 103 v.b.
    varsayılan parametre değeri: slient=False

    örnek çıktı:
        number  tradeLimit
    0   100     7248.61
    """
    print("\nAlt Hesap görüntüleme isteği atılıyor...\n")
    subAccount_result=Conn.GetSubAccounts()
    if subAccount_result:
        try:
            succ = subAccount_result["success"]
            if succ:
                content = subAccount_result["content"]
                df = pd.DataFrame(content)
                #print(df)
                return df
            else: print(f"Sub Account bilgisi çekme işlemi başarısız: {subAccount_result['message']}") 
        except Exception as e:
            print(f"Sub Account bilgisi çekme işleminde hata oluştu: {e}")

### İşlem Bilgisi
#### Günlük İşlemleri Getirme
def get_todays_transaction(subaccount:str = ""):
    """
        Günlük işlemlerinizi çekebilirsiniz.(Bekleyen gerçekleşen silinen v.b.)
        Aldığı parametre sub_account="". Varsayılan olarak boş gönderilir.

        Örnek çıktı:
            atpref ticker buysell ordersize remainingsize  price   amount      transactiontime      timetransaction       valor status waitingprice    description   transactionId equityStatusDescription shortfall timeinforce fillunit
        0   FO1NP0  SKBNK    Alış         1             1      0     3.93  30.07.2024 00:00:00  30.07.2024 15:57:11  30.07.2024  11101         3.93  İyileştirildi  20240730FO1NP0          IMPROVE_DEMAND         0           0        0
        1   FO1N6T  SKBNK    Alış         1             0      0     3.97  30.07.2024 00:00:00  30.07.2024 15:54:43  30.07.2024  00000         3.97        Silindi  20240730FO1N6T                 DELETED         0           0        0
        2   FO1MQ0  SKBNK    Alış         3             0      0    11.97  30.07.2024 00:00:00  30.07.2024 15:52:16  30.07.2024  00000         3.99        Silindi  20240730FO1MQ0                 DELETED         0           0        0
        3   FO1MCQ  SKBNK    Alış         1             0      0     3.98  30.07.2024 00:00:00  30.07.2024 15:50:29  30.07.2024  00000         3.98        Silindi  20240730FO1MCQ                 DELETED         0           0        0
        4   FO1LT0  SKBNK    Alış         1             0      0     3.95  30.07.2024 00:00:00  30.07.2024 15:47:44  30.07.2024  00000         3.95        Silindi  20240730FO1LT0                 DELETED         0           0        0
        5   FO1KW7  SKBNK    Alış         1             0      0        4  30.07.2024 00:00:00  30.07.2024 15:43:23  30.07.2024  00000            4        Silindi  20240730FO1KW7                 DELETED         0           0        0
        6   FO1KF0  SKBNK    Alış         1             0      0     4.01  30.07.2024 00:00:00  30.07.2024 15:40:49  30.07.2024  00000         4.01        Silindi  20240730FO1KF0                 DELETED         0           0        0
        7   FO1IYJ  SKBNK    Alış         1             0      0        4  30.07.2024 00:00:00  30.07.2024 15:33:51  30.07.2024  00000            4        Silindi  20240730FO1IYJ                 DELETED         0           0        0
        8   FO1HZ7  SKBNK   Satış         4             0   4.25       17  30.07.2024 00:00:00  30.07.2024 15:29:12  30.07.2024  00000         4.25    Gerçekleşti  20240730FO1HZ7                    DONE         0           0        4
        9   FO1HTT  AKBNK    Alış        25            25      0   1562.5  30.07.2024 00:00:00  30.07.2024 15:28:31  30.07.2024  11101         62.5       İletildi  20240730FO1HTT                 WAITING         0           0        0
        10  FO0YJH   DAGI   Satış       115             0    8.9  1022.35  30.07.2024 00:00:00  30.07.2024 13:53:01  30.07.2024  00000         8.89    Gerçekleşti  20240730FO0YJH                    DONE         0           0      115
        11  FO0LER   DAGI   Satış       115             0      0   1025.8  30.07.2024 00:00:00  30.07.2024 12:46:38  30.07.2024  00000         8.92        Silindi  20240730FO0LER                 DELETED         0           0        0
        12  FO0LCX  SILVR   Satış        50             0  20.84     1042  30.07.2024 00:00:00  30.07.2024 12:46:25  30.07.2024  00000        20.84    Gerçekleşti  20240730FO0LCX                    DONE         0           0       50
        13  FO0KUH   LOGO   Satış        30             0    111     3330  30.07.2024 00:00:00  30.07.2024 12:44:05  30.07.2024  00000          111    Gerçekleşti  20240730FO0KUH                    DONE         0           0       30
        14  FO0KSC  KARYE   Satış        36             0  29.22  1051.92  30.07.2024 00:00:00  30.07.2024 12:43:42  30.07.2024  00000        29.22    Gerçekleşti  20240730FO0KSC                    DONE         0           0       36
        15  FO0IDQ  SKBNK    Alış         1             0      0     4.31  30.07.2024 00:00:00  30.07.2024 12:32:38  30.07.2024  00000         4.31        Silindi  20240730FO0IDQ                 DELETED         0           0        0
        16  FO0HG8  SKBNK    Alış         1             0      0     4.31  30.07.2024 00:00:00  30.07.2024 12:27:49  30.07.2024  00000         4.31        Silindi  20240730FO0HG8                 DELETED         0           0        0
        17  FO0H5M  SKBNK    Alış         1             0      0     4.31  30.07.2024 00:00:00  30.07.2024 12:26:26  30.07.2024  00000         4.31        Silindi  20240730FO0H5M                 DELETED         0           0        0
        18  FO0GOE  SKBNK    Alış         1             0      0     4.31  30.07.2024 00:00:00  30.07.2024 12:24:13  30.07.2024  00000         4.31        Silindi  20240730FO0GOE                 DELETED         0           0        0
        19  FO0EAG  SKBNK    Alış         1             0      0     4.32  30.07.2024 00:00:00  30.07.2024 12:13:47  30.07.2024  00000         4.32        Silindi  20240730FO0EAG                 DELETED         0           0        0
        20  FO0DQ6  SKBNK    Alış         1             0      0      4.3  30.07.2024 00:00:00  30.07.2024 12:11:41  30.07.2024  00000          4.3        Silindi  20240730FO0DQ6                 DELETED         0           0        0
        21  FO0C7P  SKBNK    Alış         1             0      0     4.33  30.07.2024 00:00:00  30.07.2024 12:05:03  30.07.2024  00000         4.33        Silindi  20240730FO0C7P                 DELETED         0           0        0
        22  FO0BD7  SKBNK    Alış         2             0      0     8.64  30.07.2024 00:00:00  30.07.2024 12:01:31  30.07.2024  00000         4.32        Silindi  20240730FO0BD7                 DELETED         0           0        0
        23  FO066Z  SKBNK    Alış         1             0      0     4.33  30.07.2024 00:00:00  30.07.2024 11:40:44  30.07.2024  00000         4.33        Silindi  20240730FO066Z                 DELETED         0           0        0
        24  FO04EJ  SKBNK    Alış         1             0      0     4.35  30.07.2024 00:00:00  30.07.2024 11:34:14  30.07.2024  00000         4.35        Silindi  20240730FO04EJ                 DELETED         0           0        0
        25  FOZZCN  SKBNK    Alış         1             0   4.38     4.38  30.07.2024 00:00:00  30.07.2024 11:17:40  30.07.2024  00000         4.38    Gerçekleşti  20240730FOZZCN                    DONE         0           0        1
        26  FOZVGW  SKBNK    Alış         1             0   4.38     4.38  30.07.2024 00:00:00  30.07.2024 11:05:35  30.07.2024  00000         4.38    Gerçekleşti  20240730FOZVGW                    DONE         0           0        1
    """
    gunluk_islemler=Conn.GetTodaysTransaction(sub_account=subaccount)
    print("\nGünlük işlem listesi çekme isteği atılıyor...\n")
    if gunluk_islemler:
        try:
            succ = gunluk_islemler["success"]
            if succ:
                content = gunluk_islemler["content"]
                df = pd.DataFrame(content)
                #print(df)
                return df        
            else: print(f"Günlük işlemler başarısız oldu: {gunluk_islemler['message']}") 
        except Exception as e:
            print(f"Günlük işlemler çekilirken hata oluştu: {e}")

### Oturum Süresi Uzatma
def session_refresh(silent:bool = False):
    """
        Oturum süresi uzatmak için atılan bir istektir.
        Success:True olarak döner. (Süre uzatma işlemi başarılı olursa.)
        Success: None (Süre uzatma işlemi başarısız. Hash geçerliliğini yitirirse 401 auth hatası alırsanız. Bu durumda yeni bir token alınması gerekir.)
        Aldığı parametre: silent=False. Varsayılan olarak False gönderilir.
    """
    print("\nOturum süresi uzatma isteği atılıyor...\n")
    try:
        islem=Conn.SessionRefresh(silent=silent)
        if islem:
            print(f"Oturum süresi uzatma işlemi başarılı: {islem}")
            return islem
        else: 
            print(f"Oturum süresi uzatma işlemi başarısız: {islem}") 
    except Exception as e:
        print(f"Oturum süresi uzatma işleminde hata oluştu: {e}")

### Yeni eklenen Endpointler
#### Emir Tarihçesi Getirme
def get_equity_order_history(id:str, subaccount:str = ""):
    """
        :String id: Emrin ID’ si
        :String subAccount: Alt Hesap Numarasi “Boş gönderilebilir. Boş gönderilir ise Aktif Hesap Bilgilerini getirir.”

        Örnek Body
        {
            !!! Şuan çalışmıyor. 401 Hatası döndürüyor.
            Örnek gönen emir Referans Numarası: "FOSXEE;20240726FOSXEE - HISSEOK" 
            "id":"001VEV", (id.split(";")[0] şeklinde gönderilir.)
            "subAccount":""
        }
    """
    id = id.split(";")[0]
    print("\nPay emir Tarihçesi isteği atılıyor...\n")
    order_history=Conn.GetEquityOrderHistory(id=id,subAccount=subaccount)
    if order_history:
        try:
            succ = order_history["success"]
            if succ:
                content = order_history["content"]
                df = pd.DataFrame(content)
                #print(df) 
            else: print(f"Emir tarihçesi isteği başarısız: {order_history['message']}") 
        except Exception as e:
            print(f"Emir tarihçesi alınırken hata oluştu: {e}") 
#### Hesap Ekstresi Getirme - Hisse veya Viop Ekstresi Çekme
def account_extre(from_day:int = 7, ekstretipi:str = "accountextre"):
    """
        start_date: başlangiç tarihi "2023-07-01 00:00:00.0000" iso formatında
        end_date: bitiş tarihi "2023-07-01 00:00:00.0000" iso formatında
        days: kaç günlük ekstre çekmek istersiniz gün sayısı giriniz.
        Ekstre tipi: ekstretipi="accountextre"
        subAccount: sub_account="" varsayılan olarak boş gönderilir.

        ********************************************************************************************************************************************
        İstek Parametresi:
        Parametre Adı       Parametre       Tipi Açıklama 
        start               DateTime        Başlangıç Tarihi(iso formatında) 
        end                 DateTime        Bitiş Tarihi (iso formatında)
        subAccount          String          Alt Hesap Numarası. Boş gönderilebilir(subAccount=""). Boş gönderilir ise Aktif Hesap Bilgilerini getirir.”)

        Örnek Body: 
        {  
            "start":2023-07-01 00:00:00,  
            "end":2023-07-31 00:00:00,  
            "subAccount":""  
        }
        ********************************************************************************************************************************************
        
        Dönen Sonuç:
        Parametre Adı                   Parametre                   Tipi Açıklama 
        accountextre                    List<AccountExtre>          Hisse Ekstre 
        viopextre                       List<ViopAccountStatement>  Viop Ekstre 

        ********************************************************************************************************************************************
        
        AccountExtre: 
        Parametre Adı                   Parametre Tipi              Açıklama 
        transdate                       string                      İşlemin muhasebe tarihini 
        explanation                     string                      İşlemin açıklamasını 
        debit                           string                      İşlem ile ilgili borç miktarını 
        credit                          string                      İşlem ile ilgili alacak miktarını 
        balance                         string                      İşlem sonrasındaki hesabın bakiyesini 
        valuedate                       string                      İşlemin valör tarih ve saatini 

        ViopAccountStatement: 
        Parametre Adı                   Parametre Tipi              Açıklama 
        shortlong                       string                      Uzun kısa (Alış\Satış) sözleşme bilgisi 
        transactiondate                 string                      Emir zamanı 
        contract                        string                      İşlem yapılan sözleşme adı 
        credit                          string                      Alınan miktar 
        debit                           string                      Satılan miktar 
        units                           string                      Sözleşme adedi 
        price                           string                      Sözleşme fiyatı 
        balance                         string                      Hesap Bakiyesi 
        currency                        string                      Para birimi 

        Örnek Response: 
        {  
            "success": true,  
            "message": "Canceled",  
            "content": {  
            "accountextre": [{"transdate": "", "explanation ": "", "debit": "", "credit": "", "balance": "", "valuedate": ""}], 
            "viopextre": [{"shortlong": "", "transactiondate": "", "contract": "", "credit": "", "debit": "", "units": "", "price": "", "balance": "", "currency": ""}] 
        } }

        ********************************************************************************************************************************************

        Fonksiyonun Çıktısına Bir Örnek:
                       transdate                                            explanation        debit       credit       balance            valuedate
        0    24.07.2024 00:00:00                                                  Devir            0            0     23.000000  24.07.2024 00:00:00
        1    26.07.2024 00:00:00                                                  Devir            0            0     16.000000  26.07.2024 00:00:00
        2    26.07.2024 00:00:00                                                  Devir            0            0      5.000000  26.07.2024 00:00:00
        3    26.07.2024 00:00:00                                                  Devir            0            0    348.000000  26.07.2024 00:00:00
        4    26.07.2024 00:00:00                                                  Devir            0            0    293.000000  26.07.2024 00:00:00
        5    26.07.2024 00:00:00                                                  Devir            0            0     28.000000  26.07.2024 00:00:00
        6    26.07.2024 10:27:49                  26/07/2024 Ref = FOR8GI HS 124.900000    16.000000            0             0  30.07.2024 00:00:00
        7    01.01.0001 00:00:00                                                  Devir            0            0             0  30.07.2024 00:00:00
        8    26.07.2024 10:30:21                       26/07/2024 Ref = FOR9P9 HA 22.70            0   100.000000    100.000000  30.07.2024 00:00:00
        9    26.07.2024 11:07:29                       26/07/2024 Ref = FORGQG HA 22.40            0    50.000000    150.000000  30.07.2024 00:00:00
        10   26.07.2024 11:23:46                   26/07/2024 Ref = FORT07 HS 22.560000   150.000000            0             0  30.07.2024 00:00:00
        11   01.01.0001 00:00:00                                                  Devir            0            0             0  30.07.2024 00:00:00
        12   26.07.2024 10:18:49                       26/07/2024 Ref = FOR45B HA 38.64            0    44.000000     44.000000  30.07.2024 00:00:00
        13   26.07.2024 10:58:47                   26/07/2024 Ref = FORL1V HS 38.880000    44.000000            0             0  30.07.2024 00:00:00
        14   01.01.0001 00:00:00                                                  Devir            0            0             0  30.07.2024 00:00:00
        15   26.07.2024 14:05:34                        26/07/2024 Ref = FOSSQU HA 8.59            0            1             1  30.07.2024 00:00:00
        16   26.07.2024 14:12:58                        26/07/2024 Ref = FOSU42 HA 8.60            0            1      2.000000  30.07.2024 00:00:00
        17   26.07.2024 14:14:35                        26/07/2024 Ref = FOSUFM HA 8.62            0            1      3.000000  30.07.2024 00:00:00
        18   26.07.2024 14:23:36                    26/07/2024 Ref = FOSWFR HS 8.600000     3.000000            0             0  30.07.2024 00:00:00
        19   26.07.2024 14:28:34                        26/07/2024 Ref = FOSWTR HA 8.60            0            1             1  30.07.2024 00:00:00
        20   26.07.2024 14:29:09                    26/07/2024 Ref = FOSXEE HS 8.590000            1            0             0  30.07.2024 00:00:00
        21   01.01.0001 00:00:00                                                  Devir            0            0             0  30.07.2024 00:00:00
        22   26.07.2024 11:05:51                       26/07/2024 Ref = FORMZH HA 34.50            0    50.000000     50.000000  30.07.2024 00:00:00
        23   26.07.2024 11:24:54                   26/07/2024 Ref = FORTCW HS 34.120000    50.000000            0             0  30.07.2024 00:00:00
        24   01.01.0001 00:00:00                                                  Devir            0            0             0  30.07.2024 00:00:00
        25   26.07.2024 10:53:18                       26/07/2024 Ref = FORDR2 HA 51.30            0    30.000000     30.000000  30.07.2024 00:00:00
        26   26.07.2024 11:37:38                   26/07/2024 Ref = FORRA5 HS 51.700000    30.000000            0             0  30.07.2024 00:00:00
        27   26.07.2024 10:26:16                  26/07/2024 Ref = FOR7XB HS 348.000000     5.000000            0             0  30.07.2024 00:00:00
        28   01.01.0001 00:00:00                                                  Devir            0            0             0  30.07.2024 00:00:00
        29   26.07.2024 11:55:08                       26/07/2024 Ref = FOS0S4 HA 38.96            0    40.000000     40.000000  30.07.2024 00:00:00
        30   01.01.0001 00:00:00                                                  Devir            0            0             0  30.07.2024 00:00:00
        31   26.07.2024 10:30:40                      26/07/2024 Ref = FOR9XO HA 109.10            0    15.000000     15.000000  30.07.2024 00:00:00
        32   26.07.2024 10:46:06                      26/07/2024 Ref = FORGC2 HA 108.90            0    15.000000     30.000000  30.07.2024 00:00:00
        33   26.07.2024 10:27:16                    26/07/2024 Ref = FOR8DP HS 8.710000   348.000000            0             0  30.07.2024 00:00:00
        34   26.07.2024 11:42:14                        26/07/2024 Ref = FORUBQ HA 8.65            0   250.000000    250.000000  30.07.2024 00:00:00
        35   26.07.2024 10:26:07                   26/07/2024 Ref = FOR7UN HS 16.240000   293.000000            0             0  30.07.2024 00:00:00
        36   01.01.0001 00:00:00                                                  Devir            0            0             0  30.07.2024 00:00:00
        37   26.07.2024 10:35:35                      26/07/2024 Ref = FORADV HA 118.50            0    13.000000     13.000000  30.07.2024 00:00:00
        38   26.07.2024 11:00:02                  26/07/2024 Ref = FORLAB HS 118.800000    13.000000            0             0  30.07.2024 00:00:00
        39   26.07.2024 10:26:42                   26/07/2024 Ref = FOR847 HS 83.250000    23.000000            0             0  30.07.2024 00:00:00
        40   01.01.0001 00:00:00                                                  Devir            0            0             0  30.07.2024 00:00:00
        41   26.07.2024 10:18:49              26/07/2024 Ref = FOR45B HA 38.64x44 ARDYZ  1700.160000            0  -1700.160000  30.07.2024 00:00:00
        42   26.07.2024 10:26:07  26/07/2024 Ref = FOR7UN HS 16.240000x293.000000 MANAS            0  4758.320000   3058.160000  30.07.2024 00:00:00
        43   26.07.2024 10:26:16   26/07/2024 Ref = FOR7XB HS 348.000000x5.000000 INVES            0  1740.000000   4798.160000  30.07.2024 00:00:00
        44   26.07.2024 10:26:42          26/07/2024 Ref = FOR847 HS 83.250000x23 PASEU            0  1914.750000   6712.910000  30.07.2024 00:00:00
        45   26.07.2024 10:27:10  26/07/2024 Ref = FOR8C4 HS 133.600000x28.000000 VAKKO            0  3740.800000  10453.710000  30.07.2024 00:00:00
        46   26.07.2024 10:27:16   26/07/2024 Ref = FOR8DP HS 8.710000x348.000000 MAKTK            0  3031.080000  13484.790000  30.07.2024 00:00:00
        47   26.07.2024 10:27:49  26/07/2024 Ref = FOR8GI HS 124.900000x16.000000 AGESA            0  1998.400000  15483.190000  30.07.2024 00:00:00
        48   26.07.2024 10:30:21             26/07/2024 Ref = FOR9P9 HA 22.70x100 AGROT  2270.000000            0  13213.190000  30.07.2024 00:00:00
        49   26.07.2024 10:30:40              26/07/2024 Ref = FOR9XO HA 109.10x15 LOGO  1636.500000            0  11576.690000  30.07.2024 00:00:00
        50   26.07.2024 10:35:35              26/07/2024 Ref = FORADV HA 118.50x13 MAVI  1540.500000            0  10036.190000  30.07.2024 00:00:00
        51   26.07.2024 10:46:06              26/07/2024 Ref = FORGC2 HA 108.90x15 LOGO  1633.500000            0   8402.690000  30.07.2024 00:00:00
        52   26.07.2024 10:53:18              26/07/2024 Ref = FORDR2 HA 51.30x30 HOROZ  1539.000000            0   6863.690000  30.07.2024 00:00:00
        53   26.07.2024 10:58:47   26/07/2024 Ref = FORL1V HS 38.880000x44.000000 ARDYZ            0  1710.720000   8574.410000  30.07.2024 00:00:00
        54   26.07.2024 11:00:02   26/07/2024 Ref = FORLAB HS 118.800000x13.000000 MAVI            0  1544.400000  10118.810000  30.07.2024 00:00:00
        55   26.07.2024 11:04:25             26/07/2024 Ref = FORM5C HA 133.00x10 VAKKO  1330.000000            0   8788.810000  30.07.2024 00:00:00
        56   26.07.2024 11:05:51              26/07/2024 Ref = FORMZH HA 34.50x50 GEREL  1725.000000            0   7063.810000  30.07.2024 00:00:00
        57   26.07.2024 11:07:29              26/07/2024 Ref = FORGQG HA 22.40x50 AGROT  1120.000000            0   5943.810000  30.07.2024 00:00:00
        58   26.07.2024 11:23:46  26/07/2024 Ref = FORT07 HS 22.560000x150.000000 AGROT            0  3384.000000   9327.810000  30.07.2024 00:00:00
        59   26.07.2024 11:24:54   26/07/2024 Ref = FORTCW HS 34.120000x50.000000 GEREL            0  1706.000000  11033.810000  30.07.2024 00:00:00
        60   26.07.2024 11:27:31             26/07/2024 Ref = FORQVO HA 132.80x10 VAKKO  1328.000000            0   9705.810000  30.07.2024 00:00:00
        61   26.07.2024 11:37:38   26/07/2024 Ref = FORRA5 HS 51.700000x30.000000 HOROZ            0  1551.000000  11256.810000  30.07.2024 00:00:00
        62   26.07.2024 11:42:14              26/07/2024 Ref = FORUBQ HA 8.65x250 MAKTK  2162.500000            0   9094.310000  30.07.2024 00:00:00
        63   26.07.2024 11:55:08              26/07/2024 Ref = FOS0S4 HA 38.96x40 ISDMR  1558.400000            0   7535.910000  30.07.2024 00:00:00
        64   26.07.2024 14:05:34                 26/07/2024 Ref = FOSSQU HA 8.59x1 DAGI     8.590000            0   7527.320000  30.07.2024 00:00:00
        65   26.07.2024 14:12:58                 26/07/2024 Ref = FOSU42 HA 8.60x1 DAGI     8.600000            0   7518.720000  30.07.2024 00:00:00
        66   26.07.2024 14:14:35                 26/07/2024 Ref = FOSUFM HA 8.62x1 DAGI     8.620000            0   7510.100000  30.07.2024 00:00:00
        67   26.07.2024 14:23:36      26/07/2024 Ref = FOSWFR HS 8.600000x3.000000 DAGI            0    25.800000   7535.900000  30.07.2024 00:00:00
        68   26.07.2024 14:28:34                 26/07/2024 Ref = FOSWTR HA 8.60x1 DAGI     8.600000            0   7527.300000  30.07.2024 00:00:00
        69   26.07.2024 14:29:09      26/07/2024 Ref = FOSXEE HS 8.590000x1.000000 DAGI            0     8.590000   7535.890000  30.07.2024 00:00:00
        70   26.07.2024 20:10:32            Matrah 46691.83 Oran 0.002 Komisyon Tutarı     93.380000            0   7442.510000  30.07.2024 00:00:00
        71   26.07.2024 20:10:32                          Matrah 93.38 Kom.BSMV Tutarı      4.670000            0   7437.840000  30.07.2024 00:00:00
        72   26.07.2024 20:56:11          Matrah 8996.34Oran0.000012Hisse iptal ücreti      0.120000            0   7437.720000  30.07.2024 00:00:00
        73   26.07.2024 20:59:03                     Hisse Borsa Payı Hacimsel Komisyon     1.230000            0   7436.490000  30.07.2024 00:00:00
        74   30.07.2024 02:07:25           21469696-100 Nolu Hesabın Banka Takas İşlemi  7436.490000            0             0  30.07.2024 00:00:00
        75   26.07.2024 10:27:10                  26/07/2024 Ref = FOR8C4 HS 133.600000    28.000000            0             0  30.07.2024 00:00:00
        76   26.07.2024 11:04:25                      26/07/2024 Ref = FORM5C HA 133.00            0    10.000000     10.000000  30.07.2024 00:00:00
        77   26.07.2024 11:27:31                      26/07/2024 Ref = FORQVO HA 132.80            0    10.000000     20.000000  30.07.2024 00:00:00
        78   01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        79   29.07.2024 12:38:34                       29/07/2024 Ref = FOWMTJ HA 22.96            0    44.000000     44.000000  31.07.2024 00:00:00
        80   01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        81   29.07.2024 12:36:13                       29/07/2024 Ref = FOWMAZ HA 49.98            0    25.000000     25.000000  31.07.2024 00:00:00
        82   29.07.2024 12:40:15                        29/07/2024 Ref = FOWN6U HA 8.81            0   115.000000    115.000000  31.07.2024 00:00:00
        83   01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        84   29.07.2024 12:41:56                       29/07/2024 Ref = FOWNIR HA 20.90            0    48.000000     48.000000  31.07.2024 00:00:00
        85   01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        86   29.07.2024 12:39:06                       29/07/2024 Ref = FOWMXJ HA 23.76            0    43.000000     43.000000  31.07.2024 00:00:00
        87   01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        88   29.07.2024 12:39:27                       29/07/2024 Ref = FOWN0B HA 10.12            0   100.000000    100.000000  31.07.2024 00:00:00
        89   01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        90   29.07.2024 10:00:11                       29/07/2024 Ref = FOUT67 HA 58.00            0    18.000000     18.000000  31.07.2024 00:00:00
        91   29.07.2024 10:09:28                   29/07/2024 Ref = FOV11S HS 62.450000    18.000000            0             0  31.07.2024 00:00:00
        92   01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        93   29.07.2024 10:00:10                       29/07/2024 Ref = FOUSW1 HA 13.70            0    73.000000     73.000000  31.07.2024 00:00:00
        94   29.07.2024 11:04:09                   29/07/2024 Ref = FOVTTB HS 38.300000    40.000000            0             0  31.07.2024 00:00:00
        95   01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        96   29.07.2024 12:39:51                       29/07/2024 Ref = FOWN45 HA 28.22            0    36.000000     36.000000  31.07.2024 00:00:00
        97   29.07.2024 12:34:42                    29/07/2024 Ref = FOWLWO HS 8.290000   250.000000            0             0  31.07.2024 00:00:00
        98   01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        99   29.07.2024 12:40:40                       29/07/2024 Ref = FOWN9M HA 57.85            0    18.000000     18.000000  31.07.2024 00:00:00
        100  01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        101  29.07.2024 12:37:49                       29/07/2024 Ref = FOWMNW HA 36.20            0    30.000000     30.000000  31.07.2024 00:00:00
        102  01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        103  29.07.2024 14:03:50                       29/07/2024 Ref = FOX4YG HA 20.50            0    50.000000     50.000000  31.07.2024 00:00:00
        104  29.07.2024 10:00:09             29/07/2024 Ref = FOUSLS HA 10.13x100 YKSLN  1013.000000            0  -1013.000000  31.07.2024 00:00:00
        105  29.07.2024 10:00:10              29/07/2024 Ref = FOUSQU HA 14.91x70 ULUFA  1043.700000            0  -2056.700000  31.07.2024 00:00:00
        106  29.07.2024 10:00:10              29/07/2024 Ref = FOUSW1 HA 13.70x73 HATEK  1000.100000            0  -3056.800000  31.07.2024 00:00:00
        107  29.07.2024 10:00:11              29/07/2024 Ref = FOUT67 HA 58.00x18 FORTE  1044.000000            0  -4100.800000  31.07.2024 00:00:00
        108  29.07.2024 10:09:28   29/07/2024 Ref = FOV11S HS 62.450000x18.000000 FORTE            0  1124.100000  -2976.700000  31.07.2024 00:00:00
        109  29.07.2024 11:04:09   29/07/2024 Ref = FOVTTB HS 38.300000x40.000000 ISDMR            0  1532.000000  -1444.700000  31.07.2024 00:00:00
        110  29.07.2024 11:22:32   29/07/2024 Ref = FOW14V HS 9.780000x100.000000 YKSLN            0   978.000000   -466.700000  31.07.2024 00:00:00
        111  29.07.2024 12:34:42   29/07/2024 Ref = FOWLWO HS 8.290000x250.000000 MAKTK            0  2072.500000   1605.800000  31.07.2024 00:00:00
        112  29.07.2024 12:36:13              29/07/2024 Ref = FOWMAZ HA 49.98x25 BMSTL  1249.500000            0    356.300000  31.07.2024 00:00:00
        113  29.07.2024 12:37:49              29/07/2024 Ref = FOWMNW HA 36.20x30 PRKAB  1086.000000            0   -729.700000  31.07.2024 00:00:00
        114  29.07.2024 12:38:34              29/07/2024 Ref = FOWMTJ HA 22.96x44 BMSCH  1010.240000            0  -1739.940000  31.07.2024 00:00:00
        115  29.07.2024 12:39:06              29/07/2024 Ref = FOWMXJ HA 23.76x43 ETILR  1021.680000            0  -2761.620000  31.07.2024 00:00:00
        116  29.07.2024 12:39:27             29/07/2024 Ref = FOWN0B HA 10.12x100 EYGYO  1012.000000            0  -3773.620000  31.07.2024 00:00:00
        117  29.07.2024 12:39:51              29/07/2024 Ref = FOWN45 HA 28.22x36 KARYE  1015.920000            0  -4789.540000  31.07.2024 00:00:00
        118  29.07.2024 12:40:15               29/07/2024 Ref = FOWN6U HA 8.81x115 DAGI  1013.150000            0  -5802.690000  31.07.2024 00:00:00
        119  29.07.2024 12:40:40              29/07/2024 Ref = FOWN9M HA 57.85x18 MEKAG  1041.300000            0  -6843.990000  31.07.2024 00:00:00
        120  29.07.2024 12:41:56               29/07/2024 Ref = FOWNIR HA 20.90x48 ESEN  1003.200000            0  -7847.190000  31.07.2024 00:00:00
        121  29.07.2024 14:01:46   29/07/2024 Ref = FOX4JR HS 14.370000x70.000000 ULUFA            0  1005.900000  -6841.290000  31.07.2024 00:00:00
        122  29.07.2024 14:03:50              29/07/2024 Ref = FOX4YG HA 20.50x50 SILVR  1025.000000            0  -7866.290000  31.07.2024 00:00:00
        123  29.07.2024 22:38:07            Matrah 21291.29 Oran 0.002 Komisyon Tutarı     42.580000            0  -7908.870000  31.07.2024 00:00:00
        124  29.07.2024 22:38:07                          Matrah 42.58 Kom.BSMV Tutarı      2.130000            0  -7911.000000  31.07.2024 00:00:00
        125  30.07.2024 00:17:54          Matrah 1022.70Oran0.000012Hisse iptal ücreti      0.010000            0  -7911.010000  31.07.2024 00:00:00
        126  30.07.2024 00:20:40                     Hisse Borsa Payı Hacimsel Komisyon     0.560000            0  -7911.570000  31.07.2024 00:00:00
        127  31.07.2024 02:03:09           21469696-100 Nolu Hesabın Banka Takas İşlemi            0  7911.570000             0  31.07.2024 00:00:00
        128  01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        129  29.07.2024 10:00:10                       29/07/2024 Ref = FOUSQU HA 14.91            0    70.000000     70.000000  31.07.2024 00:00:00
        130  29.07.2024 14:01:46                   29/07/2024 Ref = FOX4JR HS 14.370000    70.000000            0             0  31.07.2024 00:00:00
        131  01.01.0001 00:00:00                                                  Devir            0            0             0  31.07.2024 00:00:00
        132  29.07.2024 10:00:09                       29/07/2024 Ref = FOUSLS HA 10.13            0   100.000000    100.000000  31.07.2024 00:00:00
        133  29.07.2024 11:22:32                    29/07/2024 Ref = FOW14V HS 9.780000   100.000000            0             0  31.07.2024 00:00:00
    """
    # Kaç Günlük ekstre çekmek istersiniz gün sayısı giriniz.
    #days=days
    
    end_date = datetime.now(timezone(timedelta(hours=3)))
    start_date = end_date - timedelta(days=from_day)
    
    print("\nHesap ekstresi çekme isteği atılıyor...\n")
    extre_result = Conn.AccountExtre(start_date=start_date, end_date=end_date)
    if extre_result:
        try:
            succ = extre_result["success"]
            if succ:
                content = extre_result['content'][ekstretipi]
                df = pd.DataFrame(content)
                # print(df)
                return df
            else:
                print(extre_result.get('message', 'Hesap özeti alma işleminde bilinmeyen bir hata oluştu.'))
        except Exception as e:
            print(f"Hesap özeti alınırken hata oluştu: {e}")
#### Nakit Bakiye Tablosu Getirme - T0, T+1, T+2 nakit bayileri getirir.
def cash_flow(subaccount:str = ""):
    """
        -Nakit Bakiye Tablosu(Cash Flow):
        - T0, T+1, T+2 nakit bayileri getirir. 
        - Bu istek, kullanıcının nakit akışını gösteren bir tablo döndürür.
        - String subAccount: Alt Hesap Numarasi “Boş gönderilebilir. 
        - SubAccount boş gönderilir ise Aktif Hesap Bilgilerini getirir.”
        
        ***************************************************************************

        İstek Parametresi 
 
        Parametre Adı           Parametre           Tipi Açıklama 
        subAccount              String              Alt Hesap Numarası (Boş gönderilebilir.(subAccount="") Boş gönderilir ise Aktif Hesap Bilgilerini getirir.) 
        
        Örnek Body: 
        {  
            "subAccount":""  
        } 
        ***************************************************************************
        Dönen Sonuç:  
        Parametre Adı       Parametre Tipi      Açıklama 
        t0                  String              T+0 anındaki nakit bakiye 
        t1                  String              T+1 anındaki nakit bakiye 
        t2                  String              T+2 anındaki nakit bakiye 

        Örnek Response: 
        {  
            "success": true,  
            "message": "Canceled",  
            "content": {"t0": "", "t1": "", "t2": ""}
        }
        ***************************************************************************
        Fonksiyon Çıktısına Örnek:
        t0        t1        t2
        0  0.00  12739.82  11671.98
    """   
    print("\nNakit Akış tablosu görüntüleme isteği atılıyor...\n")
    result=Conn.CashFlow(sub_account=subaccount)
    if result:
        try:
            succ = result["success"]
            if succ:
                content = result["content"]
                df = pd.DataFrame(content,index=[0])
                #print(df)
                return df  
            else: print(f"Nakit akış tablosu alma işlemi başarısız: {result['message']}") 
        except Exception as e:
            print(f"Nakit akış tablosu alma işleminde hata oluştu: {e}")
#### Kredi Risk Simülasyonu Tablosu Getirme
def risk_simulation(subaccount:str = ""):
    """
        İstek Parametresi 
    
    Parametre Adı Parametre Tipi Açıklama 
    Subaccount String Alt Hesap Numarası 
    “Boş gönderilebilir. Boş gönderilir ise 
    Aktif Hesap Bilgilerini getirir.” 
    
    Örnek Body: 
    {
        "Subaccount":""
    }

    Sonuç 
    
    Parametre Adı Parametre Tipi Açıklama 
    t0 String T Nakit Bakiyesi 
    t1 String T+1 Nakit Bakiyesi 
    t2 String T+2 Nakit Bakiyesi 
    t0stock String  
    t1stock String  
    t2stock String  
    t0equity String T Hisse Portföy Değeri 
    t1equity String T+1 Hisse Portföy Değeri 
    t2equity String T+2 Hisse Portföy Değeri 
    t0overall String T Overall Değeri Nakit Dahil 
    t1overall String T+1 Overall Değeri Nakit Dahil 
    t2overall String T+2 Overall Değeri Nakit Dahil 
    t0capitalrate String T Özkaynak Oranı 
    t1capitalrate String T+1 Özkaynak Oranı 
    t2capitalrate String T+2 Özkaynak Oranı 
    netoverall String Nakit Hariç Overall 
    shortfalllimit String Açığa satış sözleşmesi olan 
    müşteriler için kullanılabilir açığa 
    satış bakiyesi 
    credit0 String T Nakit Bakiyesi 
    
    Örnek Response: 
    {  
    "success": true,  
    "message": "",  
    "content":  
    [  
    {  
    "t0": "0",  
    "t1": "0",  
    "t2": "0",  
    "t0stock": "0",  
    "t1stock": "0",  
    "t2stock": "0",  
    "t0equity": "0",  
    "t1equity": "0",  
    "t2equity": "0",  
    "t0overall": "0",  
    "t1overall": "0",  
    "t2overall": "0",  
    "t0capitalrate": "0",  
    "t1capitalrate": "0",  
    "t2capitalrate": "0",  
    "netoverall": "0",  
    "shortfalllimit": "0",  
    "credit0": "0"  
    }  
    ]  
    }
    """
    print("\nKredi risk simülasyonu tablosu görüntüleme isteği atılıyor...\n")
    result=Conn.RiskSimulation(sub_account=subaccount)
    if result:
        try:
            succ = result["success"]
            if succ:
                content = result["content"]
                df = pd.DataFrame(content,index=[0])
                #print(df)
                return df
            else: print(f"Risk simulation bilgisi alma başarısız: {result['message']}") 
        except Exception as e:
            print(f"Risk simulation bilgisi alınırken hata oluştu: {e}") 
    
if __name__ == "__main__":
    try:
        Conn = API(api_key=MY_API_KEY, username=MY_USERNAME, password=MY_PASSWORD, auto_login=True, verbose=True)
        if Conn.is_alive == True:
            
            print("Giriş yapıldı.")
            """≈
            sk_order_id = send_order(symbol="SKBNK", direction="Buy", pricetype="limit", price="4.03", lot="1", sms=True, email=False)
            print(sk_order_id)
            print("********************************************************************************")
            time.sleep(15)
            
            skbnk_order_modify = modify_order(id=sk_order_id, price = "3.93", lot="", viop=False)
            print(skbnk_order_modify)
            print("********************************************************************************")
            time.sleep(15) 
            
            skbnk_order_delete = delete_order(sk_order_id)
            print(skbnk_order_delete)
            print("********************************************************************************")
            
            data = get_candle_data(symbol="THYAO", period="1440")
            print(data)
            
            thyao_info = get_equity_info(symbol="THYAO")
            print(thyao_info)
            time.sleep(0.1)
        
            portfoy = get_instant_position()
            print(portfoy)
            
            alt_hesaplat = get_subaccounts()
            print(alt_hesaplat)
        
            gunluk_islemler = get_todays_transaction()
            print(gunluk_islemler.to_string())
            
            login_refres = session_refresh(silent=False)
            print(f"Oturum süresi uzatma işlemi: {login_refres}")
        
            order_history = get_equity_order_history(id="FO3888")
            print(f"Emir geçmişi: {order_history}")
        
            hesap_ozeti = account_extre()
            print(f"Hesap özeti:\n {hesap_ozeti.to_string()}")
            
            nakit_bakiyesi = cash_flow()
            print(f"Nakit bakiyesi:\n {nakit_bakiyesi.to_string()}")
            
            risk_simulation = risk_simulation()
            print(f"Risk simulation:\n {risk_simulation.to_string()}")
            """
            data = get_todays_transaction()
            print(data)
        else:
            print("Giriş yapılamadı.")
    except Exception as e:
        print(f"Hata oluştu: {e}")