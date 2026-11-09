from database import SessionLocal, engine
import models, auth

models.Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()

    # Create Admin
    if not db.query(models.User).filter(models.User.username == "admin").first():
        db.add(models.User(username="admin", password_hash=auth.get_password_hash("admin123"), role="admin"))
        print("✅ User admin criado.")

    # Create Painéis
    if not db.query(models.Painel).first():
        db.add_all([
            models.Painel(sku="P001", fabricante="Canadian", modelo="CS6W-550MS", potencia_wp=550.0, voc_v=49.6, vmp_v=41.7, isc_a=14.0, imp_a=13.2, coef_temp_voc=-0.26),
            models.Painel(sku="P002", fabricante="Jinko", modelo="Tiger Neo 575W", potencia_wp=575.0, voc_v=51.1, vmp_v=42.8, isc_a=14.2, imp_a=13.4, coef_temp_voc=-0.25)
        ])
        print("✅ Painéis cadastrados.")

    # Create Inversor com MPPTs dinâmicas (imagem da planilha)
    if not db.query(models.Inversor).first():
        inv = models.Inversor(
            sku="INV001",
            fabricante="Huawei",
            modelo="SUN2000-10KTL-M1",
            pnom_kw=10.0,
            pmax_w=11000.0,
            vmax_v=1100.0,
            vmin_v=160.0
        )
        inv.mppts = [
            models.InversorMPPT(mppt_numero=1, icc_a=18.0, imp_a=13.5, max_strings=1),
            models.InversorMPPT(mppt_numero=2, icc_a=18.0, imp_a=13.5, max_strings=1)
        ]
        db.add(inv)
        print("✅ Inversor Huawei com 2 MPPTs cadastrado.")

    db.commit()
    db.close()

if __name__ == "__main__":
    seed()