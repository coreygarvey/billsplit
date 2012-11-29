def addMemberPayment(request):
    net = member_cost - user_cost;
    member_bill = {event=event, member=user, net=net}
    old_member_bill = MemberPayment.filter(event==event, member==user) 
    if old_member_bill:
        new_bill = MemberBillForm(member_bill, instance=old_member_bill)
        new_bill.save()
    else:
        new_bill = MemberBillForm(member_bill)
        new_bill.save()
        import pdb; pdb.set_trace()

def payment(request):
    if request.method == 'POST':
        paypalList = {}
        payment = request.POST['payment']
        event_bills = MemberBill.objects.filter(event=event)
        owed_bills = event_bills.filter(net < 0).order_by(net);
        most_owed_amount = int(owed_bills.net.min());
        while most_owed_amount <= 0:
            bills_owed_first = owed_bills.filter(net = most_owed_amount);
            number_owed_first = len(bills_owed_first);
            next_owed_amount = owed_bills.number_owed_first.net;
            delta = most_owed_amount - next_owed_amount;
            max_pay = delta/number_owed_first;
            member_payment = payment/number_owed_first;
            if member_payment <= max_pay:
                for bill in bills_owed_first:
                    member_email = bill.member.email
                    amount = member_payment;
                    paypalList['member_email'] += amount;
                    bill.net += amount;
                break
            else:
                for bill in bills_owed:
                    member_email = bill.member.email
                    amount = member_payment;
                    paypalList['member_email'] += amount
                    bill.net += amount;
        paypal_link = "actionType=PAY&cancelUrl=http://localhost:8000/register&currencyCode=USD&feesPayer=EACHRECEIVER&requestEnvelope.errorLanguage=en_US&"
        paypalFinal = {}
        bill_number = 0;
        for bill in paypalList:
            email = paypalList.keys().bill_number;
            amount = paypalList[email];
            paypal_email = 'receiverList.receiver(%d).email=%s&' % (bill_number, email);
            paypal_amount = 'receiverList.receiver(%d).amount=%s&' % (bill_number, amount);
            paypal_link = paypal_link.append(paypal_email)
            paypal_link = paypal_link.append(paypal_amount)
            bill_number += 1
            if bill_number >= 6:
                break
        paypal_link = paypal_link.append('returnUrl=http://localhost:8000/register')
            




class MemberBillForm(forms.ModelForm):
    net = forms.IntegerField()

    class Meta:
        model = MemberBill
        fields = ("net")

    def save(self, commit=True):
        bill = super(MemberBillForm, self).save(commit=False)
        bill.net = self.cleaned_data["net"]
        if commit:
            bill.save()
        return bill

class MemberBill(models.Model):
    event = models.ForeignKey(Event)
    member = models.ForeignKey(User)
    net = models.FloatField()
    
    def __str__(self):
        return '%s %s %s' % (self.event, self.member, self.net)