#include <openssl/obj_mac.h>
#include <openssl/ec.h>
#include <openssl/bn.h>
#include <openssl/pem.h>
#include <openssl/sha.h>

int sha256_file(const char *filename, unsigned char md[32]) {
  FILE *fp = NULL;
  int err = 0;
  int nbytesread;
  unsigned char buffer[32];
  SHA256_CTX sha256;
  
  if (!SHA256_Init(&sha256)) {
    goto end;
  }

  if ((fp = fopen(filename, "rb")) == NULL) {
    goto end;
  }
  while ((nbytesread = fread(buffer, 1, 32, fp))) {
    if (!SHA256_Update(&sha256, buffer, nbytesread)) {
      goto end;
    }
  }
  if (!SHA256_Final(md, &sha256)) {
    goto end;
  }

 err = 1;

 end:
 if (fp) { fclose(fp); }
 
 return err;
}


void print_instructions() {
  printf("Arguments are:\n"
         "  #1: private key filename\n"
         "  #2: message filename\n"
         "  #3: signature filename\n");
}


void print_error(const char *msg) {
  fprintf(stderr, "%s\n", msg);
}


int main(int argc, char *argv[]) {

  FILE *fp = NULL;
  char *privkey_filename = NULL;
  char *msg_filename = NULL;
  char *sig_filename;
  unsigned char sig[72] = {0};
  unsigned char md[32];
  int ret;
  unsigned int siglen;
  EC_KEY *eckey = NULL;
  BIO *in = NULL;

  /* check arguments */
  if (argc != 4) {
    print_error("Arguments are missing");
    print_instructions();
    goto end;
  }
  privkey_filename = argv[1];
  msg_filename = argv[2];
  sig_filename = argv[3];

  /* load private key from file */
  in = BIO_new(BIO_s_file());
  if ((in == NULL) ||  (BIO_read_filename(in, privkey_filename) <= 0)) {
    print_error("BIO error");
    goto end;
  }
  if ((eckey = PEM_read_bio_ECPrivateKey(in, NULL, NULL, NULL)) == NULL) {
    print_error("Error reading the private key from file");
    goto end;
  }
  
  /* sha256 of message */
  if (!sha256_file(msg_filename, md)) {
    print_error("Error: hash of the message cannot be done");
    goto end;
  }

  /* signature generation */
  ret = ECDSA_sign(0, md, 32, sig, &siglen, eckey);
  if (ret != 1) {
    print_error("Error during signature");
    goto end;
  }

  /* write signature in a file */
  fp = fopen(sig_filename, "a");
  fwrite(sig, 1, siglen, fp);

 end:
  if (in) { BIO_free(in); }
  if (eckey) { EC_KEY_free(eckey); }
  if (fp) { fclose(fp); }
  return 0;
}
