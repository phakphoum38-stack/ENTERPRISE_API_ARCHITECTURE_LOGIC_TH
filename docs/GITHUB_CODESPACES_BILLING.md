# GitHub Codespaces billing

เอกสารนี้สรุปค่าใช้จ่ายของ GitHub Codespaces, โควตารายเดือนที่รวมมากับบัญชีส่วนบุคคล, และหลักการกำหนดผู้รับผิดชอบค่าใช้จ่ายของ codespace แต่ละรายการ

## วิธีคิดการใช้งาน GitHub Codespaces

Codespace หนึ่งรายการมีค่าใช้จ่ายอยู่ 2 ส่วน:

* **Compute time**: เวลาที่ codespace อยู่ในสถานะ active และใช้ทรัพยากรประมวลผล
* **Storage**: พื้นที่จัดเก็บของ codespace หรือ prebuild ตลอดช่วงเวลาที่ resource นั้นยังคงอยู่

นอกจากนี้ prebuilds ยังใช้ GitHub Actions minutes เพิ่มเติมด้วย ดูเพิ่มที่ [About GitHub Codespaces prebuilds](https://docs.github.com/en/codespaces/prebuilding-your-codespaces/about-github-codespaces-prebuilds)

### Compute time

Compute time คือระยะเวลาที่ codespace อยู่ในสถานะ active โดย GitHub จะรวมเวลาการใช้งานแยกตาม processor type ของ codespace ทั้งหมดที่ถูกเรียกเก็บเงินกับบัญชีเดียวกัน จากนั้นรายงานยอดการใช้งานไปยังระบบ billing ทุกชั่วโมง และสรุปเรียกเก็บเป็นรายเดือน

* **Compute time:** ชั่วโมงที่รวมมากับแพ็กเกจจะรีเซ็ตกลับเต็มจำนวนเมื่อเริ่มรอบ billing ใหม่ และจะคิดกับบัญชีที่เป็นเจ้าของ codespace
* **Storage:** ค่าใช้จ่ายด้าน storage จะสะสมตลอดทั้งเดือนตามการใช้งานจริงรายชั่วโมง และจะรีเซ็ตยอดสะสมเมื่อเริ่มรอบ billing ใหม่

ดูเพิ่มที่ [Billing cycles](https://docs.github.com/en/billing/concepts/billing-cycles)

### Storage volume สำหรับ codespaces

Storage วัดแบบ time-based เป็นหน่วย GB-hours และรวมองค์ประกอบต่อไปนี้:

* ไฟล์ทั้งหมดใน codespace เช่น repository ที่ clone มาและไฟล์ configuration
* ข้อมูลที่โหลดเข้าไปใน codespace หรือถูกสร้างออกมาจากซอฟต์แวร์ที่รันใน repository
* Extensions
* Prebuilt codespaces ดูเพิ่มที่ [About GitHub Codespaces prebuilds](https://docs.github.com/en/codespaces/prebuilding-your-codespaces/about-github-codespaces-prebuilds)
* Custom dev containers ดูเพิ่มที่ [Introduction to dev containers](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers#creating-a-custom-dev-container-configuration)

### Storage volume สำหรับ codespaces ที่ใช้ custom configuration

โดยค่าเริ่มต้น codespace จะสร้างจาก default Linux image หรือ "default dev container configuration" หากเปลี่ยนไปใช้ custom dev container configuration ปริมาณ storage ที่ถูกคิดจะสูงขึ้น

* **Default Linux image:** คิดเฉพาะไฟล์ใน repository และไฟล์ที่เพิ่มเข้าไปใน codespace
* **Custom base image:** คิดรวม custom dev container เพิ่มจากไฟล์ใน repository และไฟล์ใน codespace

Container ที่อ้างอิง default image จะไม่ถูกรวมใน storage volume แม้จะเพิ่ม features ใน `devcontainer.json` ก็ตาม ดูเพิ่มที่ [Adding features to a devcontainer.json file](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/configuring-dev-containers/adding-features-to-a-devcontainer-file)

## การใช้งานฟรีและการเรียกเก็บเงินสำหรับบัญชีส่วนบุคคล

แพ็กเกจ GitHub สำหรับ organization และ enterprise **ไม่มี** free quota สำหรับ GitHub Codespaces

### Free quota

บัญชี GitHub ส่วนบุคคลทุกบัญชีจะมีโควตา compute time และ storage สำหรับ GitHub Codespaces หากใช้งานเกินจากที่รวมมา ระบบจะคิดเงินกับบัญชีส่วนบุคคลนั้น

| Account plan                      | Storage ต่อเดือน | Compute time ต่อเดือน |
| --------------------------------- | ---------------- | --------------------- |
| GitHub Free for personal accounts | 15 GB-month      | 120 hrs               |
| GitHub Pro                        | 20 GB-month      | 180 hrs               |

> [!NOTE]
> GitHub Codespaces ใช้งานไม่ได้กับ repository ที่เป็นเจ้าของโดย managed user accounts โดยตรง อย่างไรก็ตาม ในกรณีของ template repository ที่เรียกเก็บเงินผ่าน organization ผู้ใช้แบบ managed user account อาจสร้าง codespace ได้ภายใต้เงื่อนไขของ organization นั้น ดูเพิ่มที่ [About Enterprise Managed Users](https://docs.github.com/en/enterprise-cloud@latest/admin/concepts/identity-and-access-management/enterprise-managed-users)

หากต้องการใช้โควตาที่รวมมาให้คุ้มขึ้น ดู [Getting the most out of your included usage](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage)

### เมื่อใช้งานเกินโควตาที่รวมมา

หากบัญชีไม่มี valid payment method การใช้งานจะถูก block ทันทีเมื่อใช้โควตาครบ

หากคุณถูก block จากการ resume codespace แต่ยังต้องทำงานต่อ คุณสามารถเลือกได้ดังนี้:

* เพิ่ม payment method และตรวจสอบ budget settings ให้เหมาะสมกับการใช้งาน ดู [Setting up budgets to control spending on metered products](https://docs.github.com/en/billing/how-tos/set-up-budgets#viewing-budgets)
* Export การเปลี่ยนแปลงจาก codespace ไปยัง branch ดู [Exporting changes to a branch](https://docs.github.com/en/codespaces/troubleshooting/exporting-changes-to-a-branch)
* รอให้โควตารายเดือนรีเซ็ตเมื่อเริ่ม billing cycle รอบถัดไป

## การชำระเงินสำหรับ Codespaces

การใช้งาน Codespaces จะคิดผ่าน payment method ที่ตั้งไว้ในบัญชี GitHub ของคุณ ดู [Managing your payment and billing information](https://docs.github.com/en/billing/how-tos/set-up-payment/manage-payment-info)

* ประเมินค่าใช้จ่ายล่วงหน้าได้จาก [GitHub pricing calculator](https://github.com/pricing/calculator?feature=codespaces)
* ดู usage ปัจจุบันของ minutes และ storage ได้จากหมวด [View and manage paid use of GitHub products](https://docs.github.com/en/billing/how-tos/products) ซึ่งรวมลิงก์ไปยังหน้าการใช้งาน metered products และ licenses
* แนวทางลดค่าใช้จ่าย:
  * บัญชีส่วนบุคคล ดู [Getting the most out of your included usage](https://docs.github.com/en/codespaces/troubleshooting/troubleshooting-included-usage)
  * บัญชี organization ดู [Managing the cost of GitHub Codespaces in your organization](https://docs.github.com/en/codespaces/managing-codespaces-for-your-organization/managing-the-cost-of-github-codespaces-in-your-organization)

### Pricing

ค่า compute จะแปรผันตามจำนวน processor cores ของ machine type ที่เลือก ยิ่ง core มาก ราคาต่อชั่วโมงยิ่งสูง ตัวอย่างเช่น 16-core จะมีค่า compute สูงกว่า 2-core อยู่ 8 เท่า

> [!IMPORTANT]
> ตารางด้านล่างแสดงมิติการคิดราคาและตัวคูณการใช้งานที่คงอยู่ได้ยาวกว่า ส่วนตัวเลขราคาเงินจริงอาจเปลี่ยนแปลงได้ ควรตรวจสอบราคาปัจจุบันจาก [GitHub pricing calculator](https://github.com/pricing/calculator?feature=codespaces) ก่อนตัดสินใจใช้งานจริง

| Component          | Machine type | Unit of measure | Included usage multiplier |
| ------------------ | ------------ | --------------- | ------------------------- |
| Codespaces compute | 2 core       | 1 hour          | 2                         |
| Codespaces compute | 4 core       | 1 hour          | 4                         |
| Codespaces compute | 8 core       | 1 hour          | 8                         |
| Codespaces compute | 16 core      | 1 hour          | 16                        |
| Codespaces compute | 32 core      | 1 hour          | 32                        |
| Codespaces storage | Storage      | 1 GB-month      | Not applicable            |

## วิธีระบุบัญชีที่ต้องรับผิดชอบค่าใช้จ่าย

การใช้งานทั้งหมดจะถูกคิดเงินให้กับเจ้าของ codespace หรือ organization เจ้าของ repository ตามนโยบาย billing ของ organization นั้น ดู [Choosing who owns and pays for codespaces in your organization](https://docs.github.com/en/codespaces/managing-codespaces-for-your-organization/choosing-who-owns-and-pays-for-codespaces-in-your-organization)

หาก repository ถูกย้ายไปยัง organization อื่น ความเป็นเจ้าของและความรับผิดชอบด้านการเรียกเก็บเงินของ codespace ที่เกี่ยวข้องจะเปลี่ยนตามการตั้งค่าของ organization ใหม่

หากผู้ใช้ถูกลบออกจาก organization หรือ repository, codespaces ของผู้ใช้นั้นจะถูกลบโดยอัตโนมัติ

### Forked repositories

Codespace ที่สร้างจาก fork จะถูกคิดกับบัญชีส่วนบุคคลโดยค่าเริ่มต้น เว้นแต่ upstream หรือ parent repository จะอยู่ใน organization ที่อนุญาตให้คุณใช้ Codespaces โดยคิดค่าใช้จ่ายกับ organization ได้

ตัวอย่างเช่น หากสมาชิกหรือผู้ร่วมงานภายนอกของ organization ได้รับสิทธิ์ใช้ Codespaces โดยคิดกับ organization และผู้ใช้นั้นมีสิทธิ์ fork private repository ของ organization ผู้ใช้จะสามารถสร้างและใช้งาน codespace ของ repository ที่ fork มาโดยคิดค่าใช้จ่ายกับ organization ได้ เนื่องจาก parent repository ยังคงเป็นของ organization เดิม

อย่างไรก็ตาม เจ้าของ organization สามารถเพิกถอนสิทธิ์เข้าถึง repository ต้นทาง, repository ที่ fork และ codespace ที่เกี่ยวข้องได้ นอกจากนี้ยังสามารถลบ parent repository ซึ่งจะทำให้ repository ที่ fork ถูกลบตามไปด้วย โดยอ้างอิงแนวทางในหัวข้อ **Managing the forking policy for your repository** บน GitHub Docs

หากคุณสร้าง prebuilds สำหรับ forked repository ค่า storage ของ prebuilds เหล่านั้นจะถูกหักจาก included storage รายเดือนของบัญชีคุณก่อน และหากใช้ครบแล้วพร้อมเปิด billing อยู่ ระบบจะคิดเงินกับบัญชีส่วนบุคคล แม้ codespaces สำหรับ fork นั้นจะถูก organization เจ้าของ parent repository เป็นผู้จ่ายก็ตาม

### GitHub Codespaces templates

Organization ใดก็ได้สามารถดูแล template repository สำหรับ GitHub Codespaces โดย codespace ที่สร้างจาก template repository จะถูกคิดค่าใช้จ่ายกับ organization หาก organization อนุญาตให้ผู้ใช้คนนั้นใช้งานในนาม organization มิฉะนั้นจะคิดกับผู้สร้าง codespace เอง

หากผู้ใช้ publish codespace ที่สร้างจาก template ไปยัง repository ใหม่ repository นั้นจะเป็นของบัญชีส่วนบุคคลของผู้ใช้ และหาก codespace เดิมคิดค่าใช้จ่ายกับ organization ownership และ billing จะย้ายมาที่ผู้ใช้ผู้สร้าง codespace ทันที

Managed user account ไม่สามารถเป็น billable owner ของ codespace ได้ ดังนั้น:

* Managed user account จะสร้าง codespace จาก template ได้ต่อเมื่อ codespace นั้นถูกคิดกับ organization
* Managed user account ไม่สามารถ publish codespace จาก template ไปยัง repository ใหม่ได้

## การจัดการ budget สำหรับ GitHub Codespaces

หากบัญชีไม่มี valid payment method ระบบจะ block การใช้งานเมื่อใช้โควตาครบ

หากบัญชีมี valid payment method อยู่แล้ว การใช้จ่ายยังอาจถูกจำกัดด้วย budgets หนึ่งรายการหรือมากกว่า จึงควรตรวจสอบว่า budget ที่ตั้งไว้สอดคล้องกับรูปแบบการใช้งาน ดู [Setting up budgets to control spending on metered products](https://docs.github.com/en/billing/how-tos/set-up-budgets)

คุณยังสามารถรับอีเมลแจ้งเตือนเมื่อ included usage ของ GitHub Codespaces ใช้ไปถึง 90% และ 100% ของรอบ billing ปัจจุบันได้ ดู [Budgets and alerts](https://docs.github.com/en/billing/concepts/budgets-and-alerts#included-usage-alerts)

หากบัญชีส่วนบุคคล, organization หรือ enterprise ใช้ quota หรือ budget จนเต็มแล้ว จะไม่สามารถสร้างหรือ resume codespace ที่คิดค่าใช้จ่ายกับบัญชีนั้นได้อีก แต่ยังคง export งานที่ทำค้างอยู่ไปยัง branch ใหม่ได้ ดู [Exporting changes to a branch](https://docs.github.com/en/codespaces/troubleshooting/exporting-changes-to-a-branch)

## Further reading

* [Quickstart for GitHub Codespaces](https://docs.github.com/en/codespaces/quickstart)
* [Enabling or disabling GitHub Codespaces for your organization](https://docs.github.com/en/codespaces/managing-codespaces-for-your-organization/enabling-or-disabling-github-codespaces-for-your-organization)
* [Managing the cost of GitHub Codespaces in your organization](https://docs.github.com/en/codespaces/managing-codespaces-for-your-organization/managing-the-cost-of-github-codespaces-in-your-organization)
